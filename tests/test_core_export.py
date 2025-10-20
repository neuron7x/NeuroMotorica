from __future__ import annotations

from importlib import util
from pathlib import Path

import pytest

from neuromotorica.common.exceptions import MissingDependencyError
from neuromotorica.core import ExportConfig
from neuromotorica.core.export import export_to_onnx, export_to_tflite


def test_export_to_onnx_missing_dependency(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    original_find_spec = util.find_spec

    def fake_find_spec(name: str, package: str | None = None):  # type: ignore[override]
        if name == "torch":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(util, "find_spec", fake_find_spec)

    with pytest.raises(MissingDependencyError) as exc:
        export_to_onnx(object(), [], tmp_path / "model.onnx", config=ExportConfig(name="x", version="1"))
    assert exc.value.package == "torch"


def test_export_to_tflite_missing_dependency(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    original_find_spec = util.find_spec

    def fake_find_spec(name: str, package: str | None = None):  # type: ignore[override]
        if name == "tensorflow":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(util, "find_spec", fake_find_spec)

    with pytest.raises(MissingDependencyError) as exc:
        export_to_tflite(tmp_path, tmp_path / "model.tflite", config=ExportConfig(name="x", version="1"))
    assert exc.value.package == "tensorflow"
