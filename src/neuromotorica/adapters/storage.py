"""Offline-first storage primitives used by the PWA/mobile layers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class SyncEnvelope:
    id: str
    version: int
    updated_at: datetime
    payload: dict

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "version": self.version,
                "updated_at": self.updated_at.isoformat(),
                "payload": self.payload,
            },
            separators=(",", ":"),
        )


class OfflineReplica:
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _record_path(self, envelope: SyncEnvelope) -> Path:
        return self.base_path / f"{envelope.id}.json"

    def apply_batch(self, envelopes: Iterable[SyncEnvelope]) -> None:
        for envelope in envelopes:
            self._record_path(envelope).write_text(envelope.to_json(), encoding="utf-8")

    def snapshot(self) -> list[SyncEnvelope]:
        items: list[SyncEnvelope] = []
        for file in sorted(self.base_path.glob("*.json")):
            data = json.loads(file.read_text(encoding="utf-8"))
            items.append(
                SyncEnvelope(
                    id=data["id"],
                    version=int(data["version"]),
                    updated_at=datetime.fromisoformat(data["updated_at"]),
                    payload=dict(data["payload"]),
                )
            )
        return items

    @staticmethod
    def envelope_from_payload(identifier: str, version: int, payload: dict) -> SyncEnvelope:
        return SyncEnvelope(
            id=identifier,
            version=version,
            updated_at=datetime.now(timezone.utc),
            payload=payload,
        )

