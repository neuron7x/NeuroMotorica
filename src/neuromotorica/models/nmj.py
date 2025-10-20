from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from typing import Final
import numpy as np
from numpy.typing import NDArray
from .kernels import normalized_alpha_kernel, convolve_traces
from .filters import lowpass

_DEFAULT_KERNEL_DURATION: Final[float] = 0.5


def _round_for_cache(value: float) -> float:
    """Round floats to reduce floating drift in cache keys."""
    return round(float(value), 12)


@lru_cache(maxsize=128)
def _cached_normalized_kernel(
    dt: float,
    tau_rise: float,
    tau_decay: float,
    duration: float,
) -> NDArray[np.float64]:
    t = np.arange(0.0, duration, dt, dtype=np.float64)
    kernel = normalized_alpha_kernel(t, tau_rise, tau_decay)
    kernel.setflags(write=False)
    return kernel


def get_nmj_kernel(
    dt: float,
    tau_rise: float,
    tau_decay: float,
    duration: float = _DEFAULT_KERNEL_DURATION,
) -> NDArray[np.float64]:
    key = (
        _round_for_cache(dt),
        _round_for_cache(tau_rise),
        _round_for_cache(tau_decay),
        _round_for_cache(duration),
    )
    return _cached_normalized_kernel(*key)


def kernel_cache_info():
    return _cached_normalized_kernel.cache_info()


def clear_kernel_cache() -> None:
    _cached_normalized_kernel.cache_clear()


@dataclass
class NMJParams:
    quantal_content: float = 1.0
    tau_rise: float = 0.006
    tau_decay: float = 0.050
    ach_decay: float = 0.030

class NMJ:
    def __init__(
        self,
        p: NMJParams,
        dt: float,
        T: float,
        fft_threshold: int | None = None,
    ):
        if dt <= 0 or T <= 0:
            raise ValueError("dt and T must be > 0")
        self.p = p
        self.dt = dt
        self.T = T
        self.fft_threshold = int(fft_threshold) if fft_threshold is not None else 2048
        self.kernel = get_nmj_kernel(dt, p.tau_rise, p.tau_decay)

    def calcium_activation(self, spikes: NDArray[np.float64]) -> NDArray[np.float64]:
        if spikes.ndim != 2:
            raise ValueError("spikes must be [units, Tn]")
        conv = convolve_traces(
            spikes,
            self.kernel,
            use_fft_threshold=self.fft_threshold,
        )
        lp = lowpass(conv * self.p.quantal_content, self.dt, self.p.ach_decay)
        return np.clip(lp, 0.0, 1.0, out=lp)
