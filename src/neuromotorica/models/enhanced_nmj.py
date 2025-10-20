from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from .nmj import NMJ, NMJParams
from .kernels import normalized_alpha_kernel, convolve_traces
from .filters import lowpass, lowpass_biquad_filtfilt

@dataclass
class EnhancedNMJParams(NMJParams):
    co_transmission: bool = True
    ach_ratio: float = 0.7
    histamine_ratio: float = 0.3
    histamine_tau_rise: float = 0.010
    histamine_tau_decay: float = 0.080
    modulation_gain: float = 1.2

class EnhancedNMJ(NMJ):
    def __init__(self, p: EnhancedNMJParams, dt: float, T: float):
        super().__init__(p, dt, T)
        self.enhanced_p = p
        kernel_t = np.arange(0.0, 0.5, dt, dtype=np.float64)
        self.histamine_kernel = normalized_alpha_kernel(kernel_t, p.histamine_tau_rise, p.histamine_tau_decay)

    def dual_transmission_activation(self, spikes: NDArray[np.float64]) -> NDArray[np.float64]:
        if spikes.ndim != 2:
            raise ValueError("spikes must be [units, Tn]")
        ach_conv = convolve_traces(spikes, self.kernel)
        hist_conv = convolve_traces(spikes, self.histamine_kernel)
        ach_act = lowpass(
            ach_conv * self.p.quantal_content * self.enhanced_p.ach_ratio,
            self.dt,
            self.p.ach_decay,
        )
        hist_act = lowpass(
            hist_conv * self.p.quantal_content * self.enhanced_p.histamine_ratio,
            self.dt,
            self.p.ach_decay * 1.5,
        )
        combined = (ach_act + hist_act) * self.enhanced_p.modulation_gain
        return np.clip(combined, 0.0, 1.5, out=combined)

class OptimizedEnhancedNMJ(EnhancedNMJ):
    def physiologically_realistic_activation(self, spikes: NDArray[np.float64]) -> NDArray[np.float64]:
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
        combined = ach_act + hist_act + 0.3 * ach_act * hist_act
        return np.clip(combined, 0.0, 1.2, out=combined)
