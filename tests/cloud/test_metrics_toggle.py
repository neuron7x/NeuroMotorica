import sys
from types import SimpleNamespace

import pytest
from fastapi import FastAPI


@pytest.mark.parametrize(
    "enable_value, disable_value, expected",
    [
        (None, None, True),
        ("1", None, True),
        ("0", None, False),
        (None, "1", False),
        (None, "0", True),
        ("1", "1", False),
        ("0", "0", False),
    ],
)
def test_metrics_enabled(monkeypatch, enable_value, disable_value, expected):
    from neuromotorica.cloud.api import main as cloud_main

    monkeypatch.delenv("NEUROMOTORICA_ENABLE_METRICS", raising=False)
    monkeypatch.delenv("NEUROMOTORICA_DISABLE_METRICS", raising=False)

    if enable_value is not None:
        monkeypatch.setenv("NEUROMOTORICA_ENABLE_METRICS", enable_value)
    if disable_value is not None:
        monkeypatch.setenv("NEUROMOTORICA_DISABLE_METRICS", disable_value)

    assert cloud_main._metrics_enabled() is expected


def test_setup_metrics_enables_and_is_idempotent(monkeypatch):
    monkeypatch.delenv("NEUROMOTORICA_DISABLE_METRICS", raising=False)
    monkeypatch.setenv("NEUROMOTORICA_ENABLE_METRICS", "1")

    created = []
    instrumented_apps = []
    exposed_apps = []

    class DummyInstrumentator:
        def __init__(self):
            created.append(self)

        def instrument(self, app):
            instrumented_apps.append(app)
            return self

        def expose(self, app, include_in_schema=False):
            exposed_apps.append((app, include_in_schema))

    monkeypatch.setitem(
        sys.modules,
        "prometheus_fastapi_instrumentator",
        SimpleNamespace(Instrumentator=DummyInstrumentator),
    )

    from neuromotorica.cloud.api.main import _setup_metrics

    app = FastAPI()

    _setup_metrics(app)

    assert getattr(app.state, "_metrics_enabled", False) is True
    assert isinstance(app.state.metrics_instrumentator, DummyInstrumentator)
    assert created == [app.state.metrics_instrumentator]
    assert instrumented_apps == [app]
    assert exposed_apps == [(app, False)]

    _setup_metrics(app)

    assert len(created) == 1
    assert instrumented_apps == [app]
    assert exposed_apps == [(app, False)]


def test_setup_metrics_disabled_keeps_state_false(monkeypatch):
    monkeypatch.delenv("NEUROMOTORICA_ENABLE_METRICS", raising=False)
    monkeypatch.setenv("NEUROMOTORICA_DISABLE_METRICS", "1")

    from neuromotorica.cloud.api.main import _setup_metrics

    app = FastAPI()

    _setup_metrics(app)
    assert getattr(app.state, "_metrics_enabled", False) is False

    _setup_metrics(app)
    assert getattr(app.state, "_metrics_enabled", False) is False
