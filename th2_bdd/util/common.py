from datetime import datetime

from google.protobuf.timestamp_pb2 import Timestamp
from th2_grpc_check1.check1_pb2 import (
    CheckSequenceRuleRequest,
    PreFilter,
    NoMessageCheckRequest,
)
from th2_grpc_common.common_pb2 import (
    MessageFilter,
    FilterOperation,
    ValueFilter,
    ConnectionID,
)

from th2_bdd.util import sf


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


def get_check(trader, conn, checkpoint_, parent, filters, msg_type, filter_fields):
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


def get_no_message_check(trader, conn, nos_resp, parent, nos_fields):
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


def create_root(factory, name):
    root = sf.create_event_id()
    ts = Timestamp()
    ts.GetCurrentTime()
    sf.submit_event(
        estore=factory["estore"],
        event_batch=sf.create_event_batch(
            report_name=name,
            start_timestamp=ts,
            event_id=root,
        ),
    )
    return root
