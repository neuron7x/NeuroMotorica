from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import numpy.typing as npt
from numpy.typing import ArrayLike

@dataclass(frozen=True)
class SimulationMetrics:
    reps: int
    tempo: float
    range_of_motion: float
    peak_force: float

class NMJ:
    r"""
    Проста, стабільна NMJ-модель для дискретної симуляції.
    Вхід: нейронний імпульс u[t] \in [0,1]
    Вихід: скорочення м'яза y[t] \in [0,1]
    """
    def __init__(self, dt: float = 0.01, tau: float = 0.15, gain: float = 1.8, noise: float = 0.0):
        if not (0 < dt <= 0.1):
            raise ValueError("dt must be in (0,0.1]")
        if tau <= 0 or gain <= 0 or noise < 0:
            raise ValueError("Invalid tau/gain/noise")
        self.dt = dt
        self.tau = tau
        self.gain = gain
        self.noise = noise
        self.y = 0.0
        self._y_hist: list[float] = []
        self._u_hist: list[float] = []

    def reset(self) -> None:
        self.y = 0.0
        self._y_hist.clear()
        self._u_hist.clear()

    def step(self, u: float) -> float:
        u = float(np.clip(u, 0.0, 1.0))
        dy = (-(self.y) + self.gain * u) * (self.dt / self.tau)
        y = self.y + dy
        if self.noise > 0:
            y += np.random.normal(0.0, self.noise)
        self.y = float(np.clip(y, 0.0, 1.0))
        self._u_hist.append(u)
        self._y_hist.append(self.y)
        return self.y

    def simulate(self, u_seq: ArrayLike) -> npt.NDArray[np.float64]:
        self.reset()
        seq = np.asarray(u_seq, dtype=float)
        out = np.empty_like(seq, dtype=float)
        for i, u in enumerate(seq):
            out[i] = self.step(float(u))
        return cast(npt.NDArray[np.float64], out)

    def metrics(self) -> SimulationMetrics:
        if not self._y_hist:
            return SimulationMetrics(reps=0, tempo=0.0, range_of_motion=0.0, peak_force=0.0)
        y = cast(npt.NDArray[np.float64], np.asarray(self._y_hist, dtype=float))
        thr = 0.8
        ups = (y[1:] >= thr) & (y[:-1] < thr)
        reps = int(np.sum(ups))
        duration = len(y) * self.dt
        tempo = float(reps / duration) if duration > 0 else 0.0
        rom = float(np.max(y)) - float(np.min(y))
        peak = float(np.max(y))
        return SimulationMetrics(reps=reps, tempo=tempo, range_of_motion=rom, peak_force=peak)
