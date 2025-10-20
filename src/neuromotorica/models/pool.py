from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray

@dataclass
class PoolParams:
    units: int = 64
    dt: float = 0.001
    T: float = 1.0

class Pool:
    def __init__(self, units: int, dt: float, T: float):
        if units <= 0 or dt <= 0 or T <= 0:
            raise ValueError("units, dt, T must be > 0")
        self.units = units
        self.dt = dt
        self.T = T
        self.Tn = int(T / dt)

    def poisson_spikes(self, rate_hz: float, seed: int | None = None) -> NDArray[np.float64]:
        rng = np.random.default_rng(seed)
        p = rate_hz * self.dt
        return (rng.random((self.units, self.Tn)) < p).astype(np.float64)

    def single_spike(self, at_idx: int, unit_idx: int = 0) -> NDArray[np.float64]:
        """Return a spike train with a single unit firing once."""

        s = np.zeros((self.units, self.Tn), dtype=np.float64)
        if 0 <= at_idx < self.Tn and self.units:
            idx = int(np.clip(unit_idx, 0, self.units - 1))
            s[idx, at_idx] = 1.0
        return s

    def burst(self, start_idx: int, end_idx: int, units: int | None = None) -> NDArray[np.float64]:
        u = units or self.units
        s = np.zeros((u, self.Tn), dtype=np.float64)
        s[:, start_idx:end_idx] = 1.0
        return s
