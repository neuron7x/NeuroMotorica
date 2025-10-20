from __future__ import annotations
import numpy as np
from numpy.typing import NDArray


def _normalise_axis(axis: int, ndim: int) -> int:
    """Return a normalised axis index without relying on private NumPy APIs."""

    if ndim <= 0:
        raise ValueError("ndim must be > 0")

    if axis < 0:
        axis += ndim
    if axis < 0 or axis >= ndim:
        raise np.AxisError(axis, ndim=ndim)
    return int(axis)


def lowpass(
    x: NDArray[np.float64],
    dt: float,
    tau: float,
    axis: int = -1,
) -> NDArray[np.float64]:
    """First-order low-pass filter using an exact exponential discretisation."""

    if dt <= 0 or tau <= 0:
        raise ValueError("dt and tau must be > 0")

    x_arr = np.asarray(x, dtype=np.float64)
    if x_arr.ndim == 0:
        raise ValueError("x must have at least one dimension")

    axis = _normalise_axis(axis, x_arr.ndim)
    swapped = np.swapaxes(x_arr, axis, -1)
    time_len = swapped.shape[-1]
    if time_len == 0:
        return np.empty_like(x_arr)

    traces = np.ascontiguousarray(swapped.reshape(-1, time_len))
    alpha = np.exp(-dt / tau)
    alpha = float(np.clip(alpha, 0.0, 1.0))
    beta = 1.0 - alpha

    out = np.empty_like(traces)
    out[:, 0] = traces[:, 0]
    for idx in range(1, time_len):
        out[:, idx] = alpha * out[:, idx - 1] + beta * traces[:, idx]

    reshaped = out.reshape(swapped.shape)
    return np.swapaxes(reshaped, axis, -1)

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

def lowpass_biquad_filtfilt(
    x: NDArray[np.float64],
    dt: float,
    tau: float,
    Q: float = 0.707,
    axis: int = -1,
) -> NDArray[np.float64]:
    if dt <= 0 or tau <= 0:
        raise ValueError("dt and tau must be > 0")

    x_arr = np.asarray(x, dtype=np.float64)
    if x_arr.ndim == 0:
        raise ValueError("x must have at least one dimension")

    axis = _normalise_axis(axis, x_arr.ndim)
    swapped = np.swapaxes(x_arr, axis, -1)
    time_len = swapped.shape[-1]
    if time_len == 0:
        return np.empty_like(x_arr)

    fs = 1.0 / dt
    fc = 1.0 / (2 * np.pi * tau)
    b0, b1, b2, a1, a2 = _biquad_coeffs_lowpass(fc, fs, Q)

    traces = np.ascontiguousarray(swapped.reshape(-1, time_len))

    out = np.empty_like(traces)
    for i, row in enumerate(traces):
        def filt(sig: NDArray[np.float64], initial: float) -> NDArray[np.float64]:
            y = np.empty_like(sig)
            x1 = x2 = y1 = y2 = initial
            for n in range(sig.size):
                xn = float(sig[n])
                yn = b0 * xn + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
                y[n] = yn
                x2, x1 = x1, xn
                y2, y1 = y1, yn
            return y

        forward = filt(row, float(row[0]))
        backward = filt(forward[::-1], float(forward[-1]))[::-1]
        out[i] = backward

    reshaped = out.reshape(swapped.shape)
    return np.swapaxes(reshaped, axis, -1)
