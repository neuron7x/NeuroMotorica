"""Model registry utilities powering the `mlzoo/` directory."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .export import ModelArtifact


@dataclass(slots=True)
class ModelCard:
    """Lightweight metadata description for an exported model."""

    name: str
    version: str
    description: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    slug: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "ranges": {k: list(v) for k, v in self.ranges.items()},
            "tags": list(self.tags),
            "slug": self.slug or self.default_slug,
        }

    @property
    def default_slug(self) -> str:
        clean = self.name.lower().replace(" ", "-")
        return f"{clean}-v{self.version}"


class ModelRegistry:
    """Persisted mapping between model slugs and artifacts."""

    def __init__(self, registry_path: str | Path):
        self.path = Path(registry_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, dict[str, Any]] = {}
        if self.path.exists():
            self._entries = json.loads(self.path.read_text(encoding="utf-8"))

    def register(self, artifact: ModelArtifact, card: ModelCard, *, persist: bool = True) -> str:
        slug = card.slug or card.default_slug
        payload = {
            "artifact": artifact.as_dict(),
            "card": card.as_dict(),
        }
        self._entries[slug] = payload
        if persist:
            self.flush()
        return slug

    def flush(self) -> None:
        self.path.write_text(json.dumps(self._entries, indent=2, sort_keys=True), encoding="utf-8")

    def items(self) -> Iterable[tuple[str, dict[str, Any]]]:
        return self._entries.items()

    def get(self, slug: str) -> dict[str, Any] | None:
        return self._entries.get(slug)

