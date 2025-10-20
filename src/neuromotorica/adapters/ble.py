"""Cross-platform BLE adapter abstractions for Web Bluetooth and native stacks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from importlib import util
from typing import Callable, Iterable

from ..common.exceptions import MissingDependencyError


class BLECapability(str, Enum):
    HEART_RATE = "heart_rate"
    IMU = "imu"
    EMG = "emg"


@dataclass(slots=True)
class BLEDeviceProfile:
    name: str
    service_uuid: str
    characteristics: tuple[str, ...]
    capabilities: tuple[BLECapability, ...]


@dataclass(slots=True)
class BLEPacket:
    handle: int
    payload: bytes


PacketHandler = Callable[[BLEPacket], None]


class BLEAdapter:
    """Thin wrapper that maps BLE traffic into structured packets."""

    def __init__(self, profile: BLEDeviceProfile):
        self.profile = profile

    def _require_bleak(self):
        return __import__("bleak")  # noqa: PLC0414 - intentionally dynamic

    async def connect(self, address: str) -> None:
        if util.find_spec("bleak") is None:
            raise MissingDependencyError("bleak", "pip install bleak")
        self._client = self._require_bleak().BleakClient(address)
        await self._client.connect()

    async def subscribe(self, handler: PacketHandler) -> None:
        if not hasattr(self, "_client"):
            raise RuntimeError("Call connect() before subscribe().")
        client = self._client

        async def _cb(_: int, data: bytearray) -> None:  # pragma: no cover - async bridge
            handler(BLEPacket(handle=0, payload=bytes(data)))

        for characteristic in self.profile.characteristics:
            await client.start_notify(characteristic, _cb)

    async def disconnect(self) -> None:
        if hasattr(self, "_client"):
            await self._client.disconnect()


def enumerate_capabilities(profiles: Iterable[BLEDeviceProfile]) -> set[BLECapability]:
    caps: set[BLECapability] = set()
    for profile in profiles:
        caps.update(profile.capabilities)
    return caps

