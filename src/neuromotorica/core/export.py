"""Utilities that export trained policies into portable runtimes.

The export pipeline intentionally avoids hard dependencies on heavyweight ML
frameworks.  Instead, we lazily verify whether the runtime is available and
surface actionable installation hints.  This keeps the project lightweight while
still enabling full ONNX/TFLite export paths when the appropriate toolchains are
installed in the developer environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module, util
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..common.exceptions import MissingDependencyError


def _require_module(module_name: str, install_hint: str) -> Any:
    """Return a module if it is importable, otherwise raise.

    The function uses :func:`importlib.util.find_spec` to avoid wrapping imports
    with try/except blocks, as mandated by the repository coding standards.
    """

    spec = util.find_spec(module_name)
    if spec is None:
        raise MissingDependencyError(package=module_name, install_hint=install_hint)
    return import_module(module_name)


@dataclass(slots=True)
class ExportConfig:
    """Metadata describing how a model was exported."""

    name: str
    version: str
    description: str | None = None
    tags: tuple[str, ...] = ()
    quantization: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelArtifact:
    """Represents a serialized model along with metadata."""

    path: Path
    format: str
    config: ExportConfig

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "format": self.format,
            "config": {
                "name": self.config.name,
                "version": self.config.version,
                "description": self.config.description,
                "tags": list(self.config.tags),
                "quantization": self.config.quantization,
                "extras": dict(self.config.extras),
            },
        }


def export_to_onnx(
    model: Any,
    example_inputs: Iterable[Any],
    output_path: str | Path,
    *,
    opset: int = 18,
    dynamic_axes: Mapping[str, Mapping[int, str]] | None = None,
    config: ExportConfig | None = None,
) -> ModelArtifact:
    """Export a PyTorch model to an ONNX artifact."""

    torch = _require_module("torch", "pip install torch --extra-index-url https://download.pytorch.org/whl/cpu")
    onnx = _require_module("onnx", "pip install onnx")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    input_tuple = tuple(example_inputs)
    torch.onnx.export(
        model,
        input_tuple,
        output_path.as_posix(),
        opset_version=opset,
        dynamic_axes=dynamic_axes,
    )

    # Validate the produced file eagerly so that export failures surface early.
    onnx_model = onnx.load(output_path.as_posix())
    onnx.checker.check_model(onnx_model)

    if config is None:
        config = ExportConfig(name="unnamed", version="0")

    return ModelArtifact(path=output_path, format="onnx", config=config)


def export_to_tflite(
    saved_model_dir: str | Path,
    output_path: str | Path,
    *,
    quantization: str | None = None,
    representative_dataset: Iterable[Any] | None = None,
    config: ExportConfig | None = None,
) -> ModelArtifact:
    """Export a TensorFlow saved model into a (potentially quantised) TFLite file."""

    tensorflow = _require_module("tensorflow", "pip install tensorflow")

    converter = tensorflow.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
    if quantization:
        converter.optimizations = [tensorflow.lite.Optimize.DEFAULT]
        if quantization == "int8":
            if representative_dataset is None:
                raise ValueError("INT8 quantization requires a representative dataset")

            def _generator() -> Iterable[Any]:  # pragma: no cover - generator wiring
                for sample in representative_dataset:
                    yield [sample]

            converter.representative_dataset = _generator
            converter.target_spec.supported_ops = [tensorflow.lite.OpsSet.TFLITE_BUILTINS_INT8]
            converter.inference_input_type = tensorflow.uint8
            converter.inference_output_type = tensorflow.uint8

    tflite_model = converter.convert()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(tflite_model)

    if config is None:
        config = ExportConfig(name="unnamed", version="0", quantization=quantization)

    return ModelArtifact(path=output_path, format="tflite", config=config)

