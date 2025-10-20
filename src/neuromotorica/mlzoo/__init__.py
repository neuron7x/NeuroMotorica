"""Model Zoo containing portable artifacts referenced by the runtime."""

from __future__ import annotations

from pathlib import Path

REGISTRY_PATH = Path(__file__).with_name("registry.json")

__all__ = ["REGISTRY_PATH"]

