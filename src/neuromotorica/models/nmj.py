from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from .kernels import normalized_alpha_kernel, convolve_signal
from .filters import lowpass

@dataclass
class NMJParams:
    quantal_content: float = 1.0
    tau_rise: float = 0.006
    tau_decay: float = 0.050
    ach_decay: float = 0.030

class NMJ:
    def __init__(self, p: NMJParams, dt: float, T: float):
        if dt <= 0 or T <= 0:
            raise ValueError("dt and T must be > 0")
        self.p = p
        self.dt = dt
        self.T = T
        kernel_t = np.arange(0.0, 0.5, dt, dtype=np.float64)
        self.kernel = normalized_alpha_kernel(kernel_t, p.tau_rise, p.tau_decay)

    def calcium_activation(self, spikes: NDArray[np.float64]) -> NDArray[np.float64]:
        if spikes.ndim != 2:
            raise ValueError("spikes must be [units, Tn]")
        N, Tn = spikes.shape
        act = np.zeros_like(spikes, dtype=np.float64)
        for i in range(N):
            s = spikes[i, :]
            conv = convolve_signal(s, self.kernel)
            lp = lowpass(conv * self.p.quantal_content, self.dt, self.p.ach_decay)
            act[i, :] = np.clip(lp, 0.0, 1.0)
        return act
