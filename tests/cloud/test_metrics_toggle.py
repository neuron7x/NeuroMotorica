import builtins
import sys
import types

import pytest
from fastapi import FastAPI

from neuromotorica.cloud.api import main


@pytest.mark.parametrize(
    "disable_value, enable_value, expected",
    [
        ("1", None, False),
        ("false", None, True),
        (None, "1", True),
        (None, "0", False),
        (None, None, True),
        ("0", "0", False),
    ],
)
def test_metrics_enabled_env_matrix(monkeypatch, disable_value, enable_value, expected):
    if disable_value is None:
        monkeypatch.delenv("NEUROMOTORICA_DISABLE_METRICS", raising=False)
    else:
        monkeypatch.setenv("NEUROMOTORICA_DISABLE_METRICS", disable_value)

    if enable_value is None:
        monkeypatch.delenv("NEUROMOTORICA_ENABLE_METRICS", raising=False)
    else:
        monkeypatch.setenv("NEUROMOTORICA_ENABLE_METRICS", enable_value)

    assert main._metrics_enabled() is expected


def test_metrics_enabled_logs_warning_for_unknown_value(monkeypatch, caplog):
    caplog.set_level("WARNING")
    monkeypatch.setenv("NEUROMOTORICA_DISABLE_METRICS", "maybe")
    monkeypatch.delenv("NEUROMOTORICA_ENABLE_METRICS", raising=False)

    assert main._metrics_enabled() is True
    assert "Unrecognized value" in caplog.text


class _DummyInstrumentator:
    def __init__(self):
        self.instrument_called = False
        self.expose_called = False
        self.instrument_app = None
        self.expose_app = None
        self.expose_kwargs = None

    def instrument(self, app):
        self.instrument_called = True
        self.instrument_app = app
        return self

    def expose(self, app, **kwargs):
        self.expose_called = True
        self.expose_app = app
        self.expose_kwargs = kwargs
        return self


def test_setup_metrics_disabled(monkeypatch):
    app = FastAPI()
    monkeypatch.setenv("NEUROMOTORICA_DISABLE_METRICS", "yes")
    monkeypatch.delenv("NEUROMOTORICA_ENABLE_METRICS", raising=False)

    main._setup_metrics(app)

    assert not getattr(app.state, "_metrics_enabled", False)
    assert not hasattr(app.state, "metrics_instrumentator")


def test_setup_metrics_enables_once(monkeypatch):
    app = FastAPI()

    module_name = "prometheus_fastapi_instrumentator"
    dummy_instances = []

    def factory():
        inst = _DummyInstrumentator()
        dummy_instances.append(inst)
        return inst

    dummy_module = types.SimpleNamespace(Instrumentator=factory)
    monkeypatch.setitem(sys.modules, module_name, dummy_module)

    monkeypatch.setenv("NEUROMOTORICA_DISABLE_METRICS", "0")
    monkeypatch.setenv("NEUROMOTORICA_ENABLE_METRICS", "1")

    main._setup_metrics(app)
    # Second call should be a no-op because the app is already instrumented.
    main._setup_metrics(app)

    assert len(dummy_instances) == 1
    instrumentator = dummy_instances[0]

    assert getattr(app.state, "_metrics_enabled", False) is True
    assert getattr(app.state, "metrics_instrumentator", None) is instrumentator
    assert instrumentator.instrument_called is True
    assert instrumentator.expose_called is True
    assert instrumentator.instrument_app is app
    assert instrumentator.expose_app is app
    assert instrumentator.expose_kwargs == {"include_in_schema": False}


def test_setup_metrics_handles_missing_dependency(monkeypatch):
    app = FastAPI()

    module_name = "prometheus_fastapi_instrumentator"
    monkeypatch.delenv("NEUROMOTORICA_DISABLE_METRICS", raising=False)
    monkeypatch.delenv("NEUROMOTORICA_ENABLE_METRICS", raising=False)

    original_import = builtins.__import__

    def fail_import(name, *args, **kwargs):
        if name == module_name:
            raise ImportError("stubbed missing dependency")
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, module_name, raising=False)
    monkeypatch.setattr(builtins, "__import__", fail_import)

    main._setup_metrics(app)

    assert getattr(app.state, "_metrics_enabled", False) is False
    assert not hasattr(app.state, "metrics_instrumentator")
