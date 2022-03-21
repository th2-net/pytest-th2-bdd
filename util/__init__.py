import datetime
import json

from google.protobuf.timestamp_pb2 import Timestamp
from th2_data_services import DataSource, Filter
from th2_grpc_act_template.act_template_pb2 import PlaceMessageRequest
from th2_grpc_check1.check1_pb2 import (
    CheckSequenceRuleRequest,
    PreFilter,
    NoMessageCheckRequest,
)
from th2_grpc_common.common_pb2 import (
    ConnectionID,
    ValueFilter,
    MessageFilter,
    FilterOperation,
)

from th2_bdd.util import sf


def check_heartbeats(src, stream, delta, username):
    data_source = DataSource(src)
    start = datetime.datetime.utcnow() - datetime.timedelta(seconds=delta)
    end = datetime.datetime.utcnow()

    messages = data_source.get_messages_from_data_provider(
        stream=stream,
        startTimestamp=start,
        endTimestamp=end,
        filter=Filter("Type", ["Heartbeat"]),
    )
    messages = list(messages)
    if len(messages) != 0:
        messages = list(
            filter(
                lambda m: m["body"]["fields"]["header"]["messageValue"]["fields"][
                    "SenderCompID"
                ]["simpleValue"]
                == username,
                messages,
            )
        )
        return len(messages) > 0, messages
    return False, messages


def get_security_status(act, parent, security_id, alias):
    resp = act.placeSecurityStatusRequest(
        PlaceMessageRequest(
            description=f'Security check for "{security_id}"',
            connection_id=ConnectionID(session_alias=alias),
            parent_event_id=parent,
            message=sf.create_message_object(
                msg_type="SecurityStatusRequest",
                fields={
                    "SecurityID": security_id,
                    "SecurityIDSource": "8",
                    "SecurityStatusReqID": str(sf.generate_client_order_id(7)),
                    "SubscriptionRequestType": "0",
                },
                session_alias=alias,
            ),
        )
    )
    return resp.response_message.fields["SecurityTradingStatus"].simple_value


def get_ts():
    ts = Timestamp()
    ts.GetCurrentTime()
    return ts


def get_status(item):
    return "SUCCESS" if item else "FAILED"


def get_filter4rule(data):
    return {
        "header": {
            "MsgType": data.MsgType,
            "TargetCompID": data.TargetCompID,
        },
        "Text": data.Text,
        "BusinessRejectReason": data.BusinessRejectReason,
        "RefTagID": data.RefTagID,
        "RefMsgType": data.RefMsgType,
    }


def send_event(name, ctx, factory, status, body, message_ids=None):
    sf.submit_event(
        estore=factory["estore"],
        event_batch=sf.create_event_batch(
            report_name=name,
            start_timestamp=get_ts(),
            event_id=sf.create_event_id(),
            parent_id=ctx["__STEP__"],
            status=get_status(status),
            body=json.dumps(body).encode(),
            attached_messages=message_ids,
        ),
    )


def get_pmr(msg_type, fields, alias, description, ctx):
    return PlaceMessageRequest(
        description=description,
        connection_id=ConnectionID(session_alias=alias),
        parent_event_id=ctx["__STEP__"],
        message=sf.create_message_object(
            msg_type=msg_type,
            fields=fields,
            session_alias=alias,
        ),
    )


basic_header = {
    "BeginString": "FIXT.1.1",
    "SenderCompID": "*",
    "SendingTime": "*",
    "MsgSeqNum": "*",
    "BodyLength": "*",
    "MsgType": "8",
}


def get_nos_fields(base=None, **kwargs):
    # instrument=None, qty=None, price=None,
    if not base:
        fields = {
            "SecurityIDSource": "8",
            "OrdType": "2",
            "AccountType": "1",
            "OrderCapacity": "A",
            "ClOrdID": sf.generate_client_order_id(7),
            "SecondaryClOrdID": sf.generate_client_order_id(7),
            "Side": "1",
            "TransactTime": (datetime.now().isoformat()),
            "TradingParty": [
                {"PartyID": "DEMO-CONN1", "PartyIDSource": "D", "PartyRole": "76"},
                {"PartyID": "0", "PartyIDSource": "P", "PartyRole": "3"},
            ],
        }
    else:
        fields = base
    for key, value in kwargs.items():
        if value:
            fields[key] = value
    return fields


def get_check(trader, conn, checkpoint_, parent, msg_type, filter_fields):
    return CheckSequenceRuleRequest(
        description=f'Trader "{trader}" {msg_type}',
        chain_id=sf.create_chain_id(),
        connectivity_id=ConnectionID(session_alias=conn),
        checkpoint=checkpoint_.checkpoint_id,
        timeout=10000,
        parent_event_id=parent,
        pre_filter=PreFilter(
            fields={
                "header": ValueFilter(
                    message_filter=MessageFilter(
                        fields={
                            "MsgType": ValueFilter(
                                simple_filter="0",
                                operation=FilterOperation.NOT_EQUAL,
                            )
                        }
                    )
                ),
            }
        ),
        message_filters=[
            sf.create_filter_object(
                msg_type=msg_type,
                fields=filter_fields,
                key_fields_list=[],
            )
        ],
    )


def get_no_message_check(trader, conn, nos_resp, parent):
    return NoMessageCheckRequest(
        description=f'Trader "{trader}" receives no messages',
        chain_id=sf.create_chain_id(),
        connectivity_id=ConnectionID(session_alias=conn),
        checkpoint=nos_resp.checkpoint_id,
        timeout=10000,
        parent_event_id=parent,
        pre_filter=PreFilter(
            fields={
                "header": ValueFilter(
                    message_filter=MessageFilter(
                        fields={
                            "MsgType": ValueFilter(
                                simple_filter="0", operation=FilterOperation.NOT_EQUAL
                            )
                        }
                    )
                )
            }
        ),
    )
