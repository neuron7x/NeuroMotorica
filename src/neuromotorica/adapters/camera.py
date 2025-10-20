"""Camera adapters using MediaPipe/MoveNet-compatible frame streams."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(slots=True)
class CameraFrame:
    timestamp: datetime
    width: int
    height: int
    data: bytes

    @classmethod
    def from_raw(cls, width: int, height: int, data: bytes) -> "CameraFrame":
        return cls(timestamp=datetime.now(timezone.utc), width=width, height=height, data=data)


class CameraAdapter(Protocol):
    def start(self) -> None:  # pragma: no cover - interface definition
        ...

    def stop(self) -> None:  # pragma: no cover - interface definition
        ...

    def next_frame(self) -> CameraFrame | None:  # pragma: no cover - interface definition
        ...

