import os
import sys
import types

import pytest

try:  # pragma: no cover - helper for test suite bootstrapping
    import prometheus_fastapi_instrumentator  # type: ignore  # noqa: F401
except ImportError:  # pragma: no cover - executed in CI environment
    from fastapi.responses import PlainTextResponse

    class _StubInstrumentator:
        def __init__(self):
            self._instrumented_app = None

        def instrument(self, app):
            self._instrumented_app = app
            return self

        def expose(self, app, include_in_schema=False):
            if not hasattr(app.state, "_stub_metrics_route"):
                @app.get("/metrics", include_in_schema=include_in_schema)
                def _metrics_stub():  # pragma: no cover - simple stub endpoint
                    return PlainTextResponse("# HELP neuromotorica_metrics_stub 1\n")

                app.state._stub_metrics_route = True
            return self

    sys.modules["prometheus_fastapi_instrumentator"] = types.SimpleNamespace(
        Instrumentator=_StubInstrumentator
    )

# Додаємо src/ в sys.path щоб імпортувати пакет як editable install fallback
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src")
if os.path.isdir(SRC):
    sys.path.insert(0, SRC)


@pytest.fixture(scope="session")
def sample_data_dir():
    """Шлях до sample_data, якщо існує — корисно для інтеграційних тестів."""
    sd = os.path.join(ROOT, "sample_data")
    if os.path.isdir(sd):
        return sd
    pytest.skip("sample_data directory not found; skipping tests that require sample data")
