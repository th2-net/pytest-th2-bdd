import datetime
import json

from _pytest.main import Session
from google.protobuf.timestamp_pb2 import Timestamp
from pytest_bdd.parser import Feature, Scenario

from th2_bdd.table import Table
import pytest

from th2_bdd.util import sf


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


def reset_ctx(ctx: dict):
    root = ctx.pop("__ROOT__")
    ctx.clear()
    ctx["__ROOT__"] = root
    return ctx
