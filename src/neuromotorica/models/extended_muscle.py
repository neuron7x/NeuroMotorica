from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from .muscle import Muscle, MuscleParams

@dataclass
class ExtendedMuscleParams(MuscleParams):
    topography_factor: float = 1.0  # mechano-sensitivity boost

class ExtendedMuscle(Muscle):
    def __init__(self, p: ExtendedMuscleParams, dt: float, T: float, units: int):
        super().__init__(p, dt, T, units)
        self.ext_p = p

    def force(self, act: NDArray[np.float64], L: float = 1.0, V: float = 0.0):
        F_total, F_mu = super().force(act, L=L, V=V)
        return F_total * self.ext_p.topography_factor, F_mu
