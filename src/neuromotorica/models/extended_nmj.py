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
    failure_bias: float = 0.0         # probability of vesicle release failure per spike

class ExtendedOptimizedNMJ(OptimizedEnhancedNMJ):
    def __init__(self, p: ExtendedNMJParams, dt: float, T: float, rng_seed: int | None = None):
        super().__init__(p, dt, T)
        self.ext_p = p
        self._rng = np.random.default_rng(rng_seed)
        self._failure_window = max(int(round(0.008 / dt)), 1)

    def _apply_failure_bias(
        self,
        activation: NDArray[np.float64],
        spikes: NDArray[np.float64],
    ) -> tuple[NDArray[np.float64], int]:
        """Apply probabilistic vesicle failures following spike events."""

        fail_bias = float(np.clip(self.ext_p.failure_bias, 0.0, 1.0))
        if fail_bias <= 0.0:
            return activation, 0
        spike_total = int(np.count_nonzero(spikes))
        if spike_total == 0:
            return activation, 0

        failure_mask = self._rng.random(spikes.shape) < (fail_bias * spikes)
        failure_count = int(np.count_nonzero(failure_mask))
        if failure_count == 0:
            return activation, 0

        dampened = activation.copy()
        t_steps = activation.shape[1]
        for unit_idx, time_idx in np.argwhere(failure_mask):
            start = int(time_idx)
            end = min(start + self._failure_window, t_steps)
            if start >= end:
                continue
            # Gradually dampen the activation to mimic a failed release tail
            decay = np.linspace(0.2, 0.5, end - start, dtype=np.float64)
            dampened[unit_idx, start:end] *= decay
        return dampened, failure_count

    def _latency_statistics(
        self,
        spikes: NDArray[np.float64],
        activation: NDArray[np.float64],
    ) -> tuple[float, float]:
        """Estimate jitter (ms) and coefficient of variation of spike-to-peak latencies."""

        search_steps = max(int(round(0.02 / self.dt)), 1)
        latencies = []
        units = spikes.shape[0]
        for unit in range(units):
            spike_indices = np.flatnonzero(spikes[unit] > 0)
            if spike_indices.size == 0:
                continue
            for idx in spike_indices:
                start = int(idx)
                end = min(start + search_steps, activation.shape[1])
                if start >= end:
                    continue
                window = activation[unit, start:end]
                if window.size == 0:
                    continue
                rel_peak = int(np.argmax(window))
                latencies.append(rel_peak * self.dt)

        if not latencies:
            return 0.0, 0.0

        lat_arr = np.asarray(latencies, dtype=np.float64)
        jitter_ms = float(lat_arr.std(ddof=0) * 1000.0)
        mean_latency = float(lat_arr.mean())
        if mean_latency <= 0.0:
            cv_latency = 0.0
        else:
            cv_latency = float(lat_arr.std(ddof=0) / mean_latency)
        return jitter_ms, cv_latency

    def extended_activation(self, spikes: NDArray[np.float64]) -> tuple[NDArray[np.float64], dict]:
        if spikes.ndim != 2:
            raise ValueError("spikes must be [units, Tn]")
        ach_conv = convolve_traces(spikes, self.kernel)
        hist_conv = convolve_traces(spikes, self.histamine_kernel)
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

        dampened, failure_count = self._apply_failure_bias(dual_act, spikes)

        # Channel noise (Wiener process)
        noisy = add_channel_noise(dampened, self.ext_p.noise_sigma, self.dt)
        clipped = np.clip(noisy, 0.0, 1.2)

        spike_total = int(np.count_nonzero(spikes))
        failure_rate = 0.0
        if spike_total > 0:
            failure_rate = min(failure_count / spike_total, 1.0)

        m = float(np.mean(clipped))
        s = float(np.std(clipped)) or 1e-9
        snr = m / s
        jitter_ms, cv_latency = self._latency_statistics(spikes, clipped)

        stats = {
            "failure_rate": float(failure_rate),
            "snr": float(snr),
            "jitter_ms": float(jitter_ms),
            "latency_cv": float(cv_latency),
        }
        return clipped, stats
