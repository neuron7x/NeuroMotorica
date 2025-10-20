from __future__ import annotations

from pathlib import Path

from neuromotorica.core import ExportConfig, ModelArtifact
from neuromotorica.core.registry import ModelCard, ModelRegistry


def test_model_registry_roundtrip(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    registry = ModelRegistry(registry_path)
    artifact = ModelArtifact(
        path=tmp_path / "model.onnx",
        format="onnx",
        config=ExportConfig(name="policy", version="1.0.0"),
    )
    card = ModelCard(
        name="Policy", version="1.0.0", description="Test", inputs=("emg",), outputs=("cue",)
    )
    slug = registry.register(artifact, card)
    assert slug == "policy-v1.0.0"

    registry2 = ModelRegistry(registry_path)
    assert slug in dict(registry2.items())
