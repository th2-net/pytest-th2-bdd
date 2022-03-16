import json

import datetime

from th2_data_services import DataSource, Filter


import pytest
from _pytest.main import Session
from google.protobuf.timestamp_pb2 import Timestamp
from pytest_bdd.parser import Scenario, Feature
from th2_grpc_act_template.act_template_pb2 import PlaceMessageRequest
from th2_grpc_common.common_pb2 import ConnectionID

from th2_bdd.table import Table
from th2_bdd.util import sf
from th2_bdd.util.common import create_root


@pytest.fixture(autouse=True, scope="session")
def ctx(request):
    try:
        ctx_obj = request.session.th2_ctx
    except AttributeError:
        ctx_obj = {"__ROOT__": dict()}
        request.session.th2_ctx = ctx_obj
    return ctx_obj


@pytest.fixture(autouse=True, scope="session")
def factory(request):
    try:
        factory_obj = request.session.th2_factory
    except AttributeError:
        factory_obj = sf.connect(config_path="./configs/")
        request.session.th2_factory = factory_obj

    yield factory_obj
    factory_obj["factory"].close()


def pytest_bdd_before_scenario(request, feature: Feature, scenario: Scenario):
    cf = request.session.th2_factory
    reset_ctx(request.session.th2_ctx)
    th2_ctx = request.session.th2_ctx
    feature_name = str(feature.name)
    if feature_name not in th2_ctx["__ROOT__"]:
        th2_ctx["__ROOT__"][feature_name] = create_root(cf, feature_name)
    th2_ctx["__SCENARIO__"] = sf.create_event_id()
    ts = Timestamp()
    ts.GetCurrentTime()
    th2_ctx["__SCENARIO_START__"] = datetime.datetime.utcnow()
    sf.submit_event(
        estore=cf["estore"],
        event_batch=sf.create_event_batch(
            report_name=str(scenario.name),
            start_timestamp=ts,
            parent_id=th2_ctx["__ROOT__"][feature_name],
            event_id=th2_ctx["__SCENARIO__"],
        ),
    )


def pytest_bdd_before_step_call(
    request, feature, scenario, step, step_func, step_func_args
):
    cf = request.session.th2_factory
    th2_ctx = request.session.th2_ctx
    th2_ctx["__STEP__"] = sf.create_event_id()
    ts = Timestamp()
    ts.GetCurrentTime()
    step_name = str(step).replace('"', "")
    parsed = str(step_name).split("\n", maxsplit=1)
    if len(parsed) == 2:
        step_name, table = parsed
        table: Table = step_func_args["table"]
        table = table.to_table()
    else:
        step_name, table = parsed[0], None
    body = table if table else {}
    body = json.dumps([body]).encode()
    th2_ctx["__STEP_BATCH__"] = sf.create_event_batch(
        report_name=step_name,
        start_timestamp=ts,
        parent_id=th2_ctx["__SCENARIO__"],
        event_id=th2_ctx["__STEP__"],
        body=body,
    )
    sf.submit_event(
        estore=cf["estore"],
        event_batch=th2_ctx["__STEP_BATCH__"],
    )


def pytest_bdd_step_error(
    request, feature, scenario, step, step_func, step_func_args, exception
):
    th2_ctx = request.session.th2_ctx
    cf = request.session.th2_factory
    batch = th2_ctx["__STEP_BATCH__"]
    batch.events[0].status = 1
    sf.submit_event(
        estore=cf["estore"],
        event_batch=batch,
    )


def pytest_sessionstart(session: Session):
    session.th2_ctx = {"__ROOT__": dict()}


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


def reset_ctx(ctx: dict):
    root = ctx.pop("__ROOT__")
    ctx.clear()
    ctx["__ROOT__"] = root
    return ctx
