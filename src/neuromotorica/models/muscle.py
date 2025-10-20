from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray

@dataclass
class MuscleParams:
    tau_act: float = 0.015
    tau_deact: float = 0.050
    F_max: float = 1000.0
    mu_size_ratio: float = 30.0
    L0: float = 1.0
    fl_width: float = 0.25
    Vmax: float = 10.0
    c: float = 1.2
    passive_k: float = 2.5
    passive_exp: float = 2.5

class Muscle:
    def __init__(self, p: MuscleParams, dt: float, T: float, units: int):
        if dt <= 0 or T <= 0 or units <= 0:
            raise ValueError("dt, T, units must be > 0")
        self.p = p
        self.dt = dt
        self.T = T
        self.units = units
        self.mu_scales = np.linspace(1.0, p.mu_size_ratio, units).astype(np.float64)

    def force(self, act: NDArray[np.float64], L: float = 1.0, V: float = 0.0) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        if act.shape[0] != self.units:
            raise ValueError("act units mismatch")
        Tn = act.shape[1]
        F_mu = np.zeros_like(act, dtype=np.float64)
        fl = np.exp(-((L - self.p.L0) ** 2) / (2 * (self.p.fl_width ** 2)))
        denom = (self.p.Vmax + self.p.c * V)
        fv = (self.p.Vmax - V) / denom if denom != 0 else 1.0
        fv = max(fv, 0.1)
        for i in range(self.units):
            F_mu[i, :] = act[i, :] * (self.p.F_max / self.units) * self.mu_scales[i] * fl * fv
        F_passive = self.p.F_max * self.p.passive_k * (np.exp(self.p.passive_exp * max(L - self.p.L0, 0.0)) - 1.0)
        F_total = np.sum(F_mu, axis=0) + F_passive
        return F_total, F_mu
