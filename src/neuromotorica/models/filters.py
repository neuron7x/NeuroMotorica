from __future__ import annotations
import numpy as np
from numpy.typing import NDArray

def lowpass(x: NDArray[np.float64], dt: float, tau: float) -> NDArray[np.float64]:
    if dt <= 0 or tau <= 0:
        raise ValueError("dt and tau must be > 0")
    y = np.zeros_like(x, dtype=np.float64)
    a = dt / tau
    for i in range(1, len(x)):
        y[i] = y[i-1] + a * (x[i] - y[i-1])
    return y

def _biquad_coeffs_lowpass(fc: float, fs: float, Q: float = 0.707):
    import numpy as np
    w0 = 2 * np.pi * fc / fs
    alpha = np.sin(w0) / (2 * Q)
    cosw0 = np.cos(w0)
    b0 = (1 - cosw0) / 2
    b1 = 1 - cosw0
    b2 = (1 - cosw0) / 2
    a0 = 1 + alpha
    a1 = -2 * cosw0
    a2 = 1 - alpha
    return (b0/a0, b1/a0, b2/a0, a1/a0, a2/a0)

def lowpass_biquad_filtfilt(x: NDArray[np.float64], dt: float, tau: float, Q: float = 0.707) -> NDArray[np.float64]:
    if dt <= 0 or tau <= 0:
        raise ValueError("dt and tau must be > 0")
    fs = 1.0 / dt
    fc = 1.0 / (2 * np.pi * tau)
    b0, b1, b2, a1, a2 = _biquad_coeffs_lowpass(fc, fs, Q)
    def filt(sig: NDArray[np.float64]) -> NDArray[np.float64]:
        y = np.zeros_like(sig, dtype=np.float64)
        x1 = x2 = y1 = y2 = 0.0
        for n in range(len(sig)):
            xn = float(sig[n])
            yn = b0*xn + b1*x1 + b2*x2 - a1*y1 - a2*y2
            y[n] = yn
            x2, x1 = x1, xn
            y2, y1 = y1, yn
        return y
    y_fwd = filt(x)
    y_bwd = filt(y_fwd[::-1])[::-1]
    return y_bwd
