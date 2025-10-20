"""Common exception definitions used across NeuroMotorica modules.

The goal is to keep domain-specific error types in a single location so they
can be reused by both the cloud-facing services and the on-device runtimes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MissingDependencyError(RuntimeError):
    """Raised when an optional dependency required for a feature is absent."""

    package: str
    install_hint: str

    def __post_init__(self) -> None:  # pragma: no cover - simple validation
        if not self.package:
            raise ValueError("package must be a non-empty string")
        if not self.install_hint:
            raise ValueError("install_hint must be a non-empty string")

    def __str__(self) -> str:
        return (
            f"Missing optional dependency '{self.package}'. "
            f"Install it via `{self.install_hint}` to enable this feature."
        )

