from __future__ import annotations
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
    if abs(td - tr) < 1e-9:
        return tr  # approx peak near tr when tr≈td
    return (tr * td) * np.log(td / tr) / (td - tr)

def normalized_alpha_kernel(t: NDArray[np.float64], tau_rise: float, tau_decay: float) -> NDArray[np.float64]:
    k = alpha_kernel(t, tau_rise, tau_decay)
    tr, td = float(tau_rise), float(tau_decay)
    tp = max(_t_peak(tr, td), 1e-12)
    # Direct evaluation at t_peak
    peak = (1.0 - np.exp(-tp / tr)) * np.exp(-tp / td)
    if not np.isfinite(peak) or peak <= 0:
        peak = float(np.max(k)) if np.max(k) > 0 else 1.0
    return (k / peak).astype(np.float64, copy=False)

def convolve_signal(sig: NDArray[np.float64], kernel: NDArray[np.float64], use_fft_threshold: int = 2048) -> NDArray[np.float64]:
    """Adaptive conv: np.convolve for short; FFT conv for long sequences.
    Returns 'full' trimmed to len(sig).
    """
    n = len(sig) + len(kernel) - 1
    if n < use_fft_threshold:
        return np.convolve(sig, kernel, mode='full')[: len(sig)]
    # FFT-based linear convolution
    # Next power of two for speed
    L = 1 << (int(np.ceil(np.log2(n))))
    Sf = np.fft.rfft(sig, n=L)
    Kf = np.fft.rfft(kernel, n=L)
    Yf = Sf * Kf
    y = np.fft.irfft(Yf, n=L)[: len(sig) + len(kernel) - 1]
    return y[: len(sig)]
