import numpy as np

from neuromotorica.models.nmj import (
    NMJ,
    NMJParams,
    clear_kernel_cache,
    kernel_cache_info,
)
from neuromotorica.models.enhanced_nmj import EnhancedNMJ, EnhancedNMJParams, OptimizedEnhancedNMJ
from neuromotorica.analysis.validation import scenario_sim


def test_nmj_kernel_cache_hits():
    clear_kernel_cache()
    dt, T = 0.001, 0.5
    nmj1 = NMJ(NMJParams(), dt, T)
    info_after_first = kernel_cache_info()
    assert info_after_first.misses == 1

    nmj2 = NMJ(NMJParams(), dt, T)
    info_after_second = kernel_cache_info()
    assert info_after_second.hits >= 1
    assert nmj1.kernel is nmj2.kernel


def test_nmj_fft_threshold_override(monkeypatch):
    thresholds: list[int] = []

    def fake_convolve(traces, kernel, use_fft_threshold):
        thresholds.append(use_fft_threshold)
        return np.zeros_like(traces)

    monkeypatch.setattr("neuromotorica.models.nmj.convolve_traces", fake_convolve)

    dt, T = 0.001, 0.2
    spikes = np.zeros((4, int(T / dt)), dtype=np.float64)
    nmj = NMJ(NMJParams(), dt, T, fft_threshold=128)
    nmj.calcium_activation(spikes)

    assert thresholds == [128]


def test_enhanced_nmj_fft_threshold(monkeypatch):
    thresholds: list[int] = []

    def fake_convolve(traces, kernel, use_fft_threshold):
        thresholds.append(use_fft_threshold)
        return np.zeros_like(traces)

    monkeypatch.setattr("neuromotorica.models.enhanced_nmj.convolve_traces", fake_convolve)

    dt, T = 0.001, 0.2
    spikes = np.zeros((4, int(T / dt)), dtype=np.float64)
    enm = EnhancedNMJ(EnhancedNMJParams(), dt, T, fft_threshold=512)
    enm.dual_transmission_activation(spikes)

    assert thresholds == [512, 512]


def test_scenario_sim_propagates_fft_threshold(monkeypatch):
    recorded: list[tuple[str, int]] = []

    original_nmj_init = NMJ.__init__

    def recording_nmj_init(self, p, dt, T, fft_threshold=None):  # type: ignore[override]
        recorded.append(("base", fft_threshold))
        original_nmj_init(self, p, dt, T, fft_threshold=fft_threshold)

    monkeypatch.setattr(NMJ, "__init__", recording_nmj_init)

    original_enh_init = EnhancedNMJ.__init__

    def recording_enh_init(self, p, dt, T, fft_threshold=None):  # type: ignore[override]
        recorded.append(("enh", fft_threshold))
        original_enh_init(self, p, dt, T, fft_threshold=fft_threshold)

    monkeypatch.setattr(EnhancedNMJ, "__init__", recording_enh_init)

    original_opt_init = OptimizedEnhancedNMJ.__init__

    def recording_opt_init(self, p, dt, T, fft_threshold=None):  # type: ignore[override]
        recorded.append(("opt", fft_threshold))
        original_opt_init(self, p, dt, T, fft_threshold=fft_threshold)

    monkeypatch.setattr(OptimizedEnhancedNMJ, "__init__", recording_opt_init)

    scenario_sim(seconds=0.05, dt=0.001, units=8, rate_hz=5, fft_threshold=1024)

    assert recorded
    assert {label for label, _ in recorded} == {"base", "enh", "opt"}
    assert all(threshold == 1024 for _, threshold in recorded)
