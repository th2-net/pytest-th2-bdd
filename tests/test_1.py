from pytest_bdd import scenario, given, when, then, parsers
from th2_grpc_check1.check1_service import Check1Service
from th2_grpc_common.common_pb2 import MessageID, ConnectionID

from tests.data import (
    UserNameRow,
    TagsRow,
    RejectRow,
    conns,
    conn_by_trader,
    ds,
    statuses,
)
from util import (
    check_heartbeats,
    get_security_status,
    get_filter4rule,
    send_event,
    get_pmr,
    get_nos_fields,
    get_check,
    get_no_message_check,
)
from th2_bdd.util import sf
from th2_bdd.table import Table


@scenario(
    "scenarios/ts01_session_management.feature",
    "TC01 Order is rejected on trading halt session",
    features_base_dir=".",
)
def test_nos():
    pass


@given(
    parsers.cfparse(
        "following users are logged in to {gateway} gateway\n{table}",
    ),
    converters={"table": Table(UserNameRow)},
)
def logged_check(factory, ctx, table: Table[UserNameRow], gateway):
    def extract_message_id(m):
        separated = m["messageId"].rsplit(":", maxsplit=2)
        direction = separated[-2].upper()
        seq = int(separated[-1])
        return MessageID(
            connection_id=ConnectionID(session_alias=m["sessionId"]),
            direction=direction,
            sequence=seq,
        )

    uname = table[0].UserName
    conn = conns[gateway]
    conn_by_trader[uname] = conn

    status, messages = check_heartbeats(ds, conn, 60, uname)
    messages_ids = [extract_message_id(m) for m in messages]
    send_event(
        f"Ensure that user {uname} is logged in",
        ctx,
        factory,
        status,
        [
            {
                "type": "message",
                "data": "Heartbeats found" if status else "Heartbeats not found",
            }
        ],
        message_ids=messages_ids,
    )


@given(
    parsers.cfparse("{instrument} is {status} (SecurityTradingStatus = {status_digit})")
)
def check_instrument_status(factory, ctx, instrument, status, status_digit):
    expected = statuses[status]
    actual = get_security_status(
        factory["act"], ctx, instrument, alias=conn_by_trader["DEMO-CONN1"]
    )
    ctx["instrument"] = instrument
    assert expected == actual


@when(
    parsers.cfparse(
        "user {username} sends a new order with the following details\n{table}"
    ),
    converters={"table": Table(TagsRow)},
    target_fixture="checkpoint",
)
def send_nos(factory, ctx, username, table: Table[TagsRow]):
    qty, price = table[0].OrderQty, table[0].Price
    nos = get_nos_fields(SecurityID=ctx["instrument"], OrderQty=qty, Price=price)
    req = get_pmr(
        msg_type="NewOrderSingle",
        fields=nos,
        alias=conn_by_trader[username],
        description=f'Trader "{username}" sends request to create order.',
        ctx=ctx,
    )
    ctx["nos_fields"] = nos
    response = sf.sendMessage(
        act=factory["act"],
        place_message_request=req,
    )
    return response


@then(
    parsers.cfparse("{username} receives {message_type} with given details\n{table}"),
    converters={"table": Table(RejectRow)},
)
def received_message_check(
    factory, ctx, message_type, username, table: Table[RejectRow], checkpoint
):
    row: RejectRow = table[0]
    sf.submitCheckSequenceRule(
        check=factory["check"],
        check_sequence_rule_request=get_check(
            username,
            conn_by_trader[username],
            checkpoint,
            ctx,
            message_type,
            get_filter4rule(row),
        ),
    )


@then(parsers.cfparse("{username} user will not receive any messages"))
def no_messages_check(factory, ctx, username, checkpoint):
    check: Check1Service = factory["check"]
    check.submitNoMessageCheck(
        get_no_message_check(
            username,
            conn_by_trader[username],
            checkpoint,
            ctx,
        ),
    )
