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
    failure_bias: float = 0.0         # baseline failure probability boost

class ExtendedOptimizedNMJ(OptimizedEnhancedNMJ):
    def __init__(self, p: ExtendedNMJParams, dt: float, T: float, *, fft_threshold: int | None = None):
        super().__init__(p, dt, T, fft_threshold=fft_threshold)
        self.ext_p = p

    def _activation_jitter_ms(self, activations: NDArray[np.float64]) -> float:
        if activations.size == 0:
            return 0.0
        dt = self.dt
        onsets: list[int] = []
        for unit_act in activations:
            peak_idx = int(np.argmax(unit_act))
            peak_val = float(unit_act[peak_idx]) if unit_act.size else 0.0
            if peak_val <= 0.0:
                continue
            threshold = 0.5 * peak_val
            search_slice = unit_act[: peak_idx + 1]
            crossings = np.flatnonzero(search_slice >= threshold)
            onset_idx = int(crossings[0]) if crossings.size else peak_idx
            onsets.append(onset_idx)
        if not onsets:
            return 0.0
        onset_arr = np.asarray(onsets, dtype=np.float64) * dt * 1000.0
        return float(np.std(onset_arr, dtype=np.float64))

    def extended_activation(
        self,
        spikes: NDArray[np.float64],
        *,
        failure_bias: float | None = None,
        fft_threshold: int | None = None,
    ) -> tuple[NDArray[np.float64], float, float, float]:
        if spikes.ndim != 2:
            raise ValueError("spikes must be [units, Tn]")
        threshold = self.fft_threshold if fft_threshold is None else max(int(fft_threshold), 1)
        ach_conv = convolve_traces(spikes, self.kernel, use_fft_threshold=threshold)
        hist_conv = convolve_traces(spikes, self.histamine_kernel, use_fft_threshold=threshold)
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
        bias = self.ext_p.failure_bias if failure_bias is None else float(failure_bias)
        failure_rate = float(np.clip(failures + max(bias, 0.0), 0.0, 1.0))
        # SNR-like metric (mean/std across all units/time)
        m = float(np.mean(clipped)); s = float(np.std(clipped)) or 1e-9
        snr = m / s
        jitter_ms = self._activation_jitter_ms(clipped)

        return clipped, failure_rate, float(snr), jitter_ms
