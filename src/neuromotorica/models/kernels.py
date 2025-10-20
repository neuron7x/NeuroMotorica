from __future__ import annotations

from functools import lru_cache

import numpy as np
from numpy.typing import NDArray

def alpha_kernel(t: NDArray[np.float64], tau_rise: float, tau_decay: float) -> NDArray[np.float64]:
    """Stable alpha-like kernel ~ (1 - e^{-t/tr}) e^{-t/td}, t>=0.
    Numerically stable near tau_rise ≈ tau_decay.
    """
    if tau_rise <= 0 or tau_decay <= 0:
        raise ValueError("tau_rise and tau_decay must be > 0")
    if np.any(t < 0):
        raise ValueError("t must be >= 0")
    tr, td = float(tau_rise), float(tau_decay)
    # Use difference of exponentials with stability guards
    up = 1.0 - np.exp(-t / tr)
    down = np.exp(-t / td)
    k = up * down
    k[t < 0] = 0.0
    return k.astype(np.float64, copy=False)

def _t_peak(tr: float, td: float) -> float:
    ratio = tr / (tr + td)
    ratio = np.clip(ratio, 1e-12, 1 - 1e-12)
    return -tr * float(np.log(ratio))

def normalized_alpha_kernel(t: NDArray[np.float64], tau_rise: float, tau_decay: float) -> NDArray[np.float64]:
    k = alpha_kernel(t, tau_rise, tau_decay)
    tr, td = float(tau_rise), float(tau_decay)
    tp = max(_t_peak(tr, td), 1e-12)
    # Direct evaluation at t_peak
    peak = (1.0 - np.exp(-tp / tr)) * np.exp(-tp / td)
    if not np.isfinite(peak) or peak <= 0:
        peak = float(np.max(k)) if np.max(k) > 0 else 1.0
    return (k / peak).astype(np.float64, copy=False)


def _round_float(value: float) -> float:
    """Round floating values for use as cache keys."""

    return float(round(value, 12))


@lru_cache(maxsize=256)
def _cached_kernel(duration: float, dt: float, tau_rise: float, tau_decay: float) -> NDArray[np.float64]:
    t = np.arange(0.0, duration, dt, dtype=np.float64)
    return normalized_alpha_kernel(t, tau_rise, tau_decay)


def cached_normalized_kernel(duration: float, dt: float, tau_rise: float, tau_decay: float) -> NDArray[np.float64]:
    """Return a cached normalized kernel for the given parameters."""

    return _cached_kernel(
        _round_float(duration),
        _round_float(dt),
        _round_float(tau_rise),
        _round_float(tau_decay),
    ).copy()

def convolve_signal(
    sig: NDArray[np.float64],
    kernel: NDArray[np.float64],
    use_fft_threshold: int = 2048,
) -> NDArray[np.float64]:
    """Adaptive conv: np.convolve for short; FFT conv for long sequences.
    Returns 'full' trimmed to len(sig)."""

    n = len(sig) + len(kernel) - 1
    if n < use_fft_threshold:
        return np.convolve(sig, kernel, mode="full")[: len(sig)]

    # FFT-based linear convolution
    L = 1 << int(np.ceil(np.log2(n)))
    spectrum_sig = np.fft.rfft(sig, n=L)
    spectrum_kernel = np.fft.rfft(kernel, n=L)
    y = np.fft.irfft(spectrum_sig * spectrum_kernel, n=L)
    return y[: len(sig)]


def convolve_traces(
    traces: NDArray[np.float64],
    kernel: NDArray[np.float64],
    use_fft_threshold: int = 2048,
) -> NDArray[np.float64]:
    """Vectorised convolution of multiple traces with a shared kernel."""

    traces_arr = np.asarray(traces, dtype=np.float64)
    kernel_arr = np.asarray(kernel, dtype=np.float64)
    if kernel_arr.ndim != 1:
        raise ValueError("kernel must be 1-D")
    if traces_arr.ndim == 0:
        raise ValueError("traces must have at least one dimension")
    if traces_arr.ndim == 1:
        return convolve_signal(traces_arr, kernel_arr, use_fft_threshold)

    time_len = traces_arr.shape[-1]
    if time_len == 0:
        return np.empty_like(traces_arr)

    n = time_len + kernel_arr.size - 1
    if n < use_fft_threshold:
        return np.apply_along_axis(
            lambda sig: np.convolve(sig, kernel_arr, mode="full")[:time_len],
            axis=-1,
            arr=traces_arr,
        )

    L = 1 << int(np.ceil(np.log2(n)))
    traces_fft = np.fft.rfft(traces_arr, n=L, axis=-1)
    kernel_fft = np.fft.rfft(kernel_arr, n=L)
    y = np.fft.irfft(traces_fft * kernel_fft, n=L, axis=-1)
    return y[..., :time_len]
