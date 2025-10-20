from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from .enhanced_nmj import EnhancedNMJParams, OptimizedEnhancedNMJ
from .filters import lowpass_biquad_filtfilt
from .kernels import convolve_traces

def add_channel_noise(x: NDArray[np.float64], sigma: float, dt: float) -> NDArray[np.float64]:
    """Vectorized Wiener noise along time axis (axis=1)."""
    if sigma <= 0:
        return x
    rng = np.random.default_rng()
    noise = rng.normal(0.0, sigma * np.sqrt(dt), size=x.shape).astype(np.float64)
    noise = np.cumsum(noise, axis=1)
    y = x + noise
    return np.clip(y, 0.0, 1.2)

@dataclass
class ExtendedNMJParams(EnhancedNMJParams):
    noise_sigma: float = 0.05         # channel noise
    glial_mod_gain: float = 0.25      # tripartite modulation

class ExtendedOptimizedNMJ(OptimizedEnhancedNMJ):
    def __init__(
        self,
        p: ExtendedNMJParams,
        dt: float,
        T: float,
        fft_threshold: int | None = None,
    ):
        super().__init__(p, dt, T, fft_threshold=fft_threshold)
        self.ext_p = p

    def extended_activation(self, spikes: NDArray[np.float64]) -> tuple[NDArray[np.float64], float, float]:
        if spikes.ndim != 2:
            raise ValueError("spikes must be [units, Tn]")
        ach_conv = convolve_traces(
            spikes,
            self.kernel,
            use_fft_threshold=self.fft_threshold,
        )
        hist_conv = convolve_traces(
            spikes,
            self.histamine_kernel,
            use_fft_threshold=self.fft_threshold,
        )
        ach_act = lowpass_biquad_filtfilt(
            ach_conv * self.p.quantal_content * self.enhanced_p.ach_ratio,
            self.dt,
            self.p.ach_decay,
        )
        hist_act = lowpass_biquad_filtfilt(
            hist_conv * self.p.quantal_content * self.enhanced_p.histamine_ratio,
            self.dt,
            self.p.ach_decay * 1.5,
        )
        glial_boost = self.ext_p.glial_mod_gain * np.mean(hist_act, axis=1, keepdims=True)
        dual_act = ach_act + hist_act + 0.3 * ach_act * hist_act + glial_boost

        # Channel noise (Wiener process)
        noisy = add_channel_noise(dual_act, self.ext_p.noise_sigma, self.dt)
        clipped = np.clip(noisy, 0.0, 1.2)

        # Failure probability: sharp negative drops across all units
        diffs = np.diff(clipped, axis=1)
        failures = (diffs < -0.1).mean() if diffs.size else 0.0
        # SNR-like metric (mean/std across all units/time)
        m = float(np.mean(clipped)); s = float(np.std(clipped)) or 1e-9
        snr = m / s

        return clipped, float(failures), float(snr)
