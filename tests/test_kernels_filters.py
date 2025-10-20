import numpy as np
from neuromotorica.models.kernels import (
    alpha_kernel,
    normalized_alpha_kernel,
    convolve_signal,
    convolve_traces,
)
from neuromotorica.models.filters import lowpass, lowpass_biquad_filtfilt

def test_alpha_kernels_normalized_and_stable_close_taus():
    t = np.linspace(0, 0.5, 1000, dtype=np.float64)
    # Near-degenerate case tau_rise≈tau_decay must be stable and normalized
    k = normalized_alpha_kernel(t, 0.02, 0.021)
    assert np.isfinite(k).all()
    assert k.max() > 0.99 and k.max() < 1.01
    # baseline too
    kb = alpha_kernel(t, 0.02, 0.021)
    assert np.isfinite(kb).all()

def test_lowpass_filters_behaviour_and_conv_equivalence():
    x = np.zeros(4096, dtype=np.float64)
    x[100:] = 1.0
    y1 = lowpass(x, dt=0.001, tau=0.03)
    y2 = lowpass_biquad_filtfilt(x, dt=0.001, tau=0.03)
    assert 0.85 <= y1[-1] <= 1.0
    assert 0.85 <= y2[-1] <= 1.0
    # Conv equivalence (FFT vs direct) for a random signal
    rng = np.random.default_rng(0)
    sig = rng.standard_normal(5000).astype(np.float64)
    k = normalized_alpha_kernel(np.linspace(0, 0.5, 500), 0.005, 0.05)
    d = np.convolve(sig, k, mode="full")[: len(sig)]
    f = convolve_signal(sig, k, use_fft_threshold=256)
    rmse = np.sqrt(np.mean((d - f) ** 2))
    assert rmse < 1e-9


def test_convolve_traces_batch_matches_rowwise():
    rng = np.random.default_rng(123)
    sig = rng.standard_normal((4, 512)).astype(np.float64)
    kernel = normalized_alpha_kernel(np.linspace(0, 0.2, 128), 0.01, 0.04)
    batch = convolve_traces(sig, kernel, use_fft_threshold=4096)
    expected = np.stack([convolve_signal(row, kernel) for row in sig], axis=0)
    assert np.allclose(batch, expected)


def test_lowpass_vectorised_axis_matches_individual_rows():
    rng = np.random.default_rng(77)
    sig = rng.standard_normal((3, 256))
    vectorised = lowpass(sig, dt=0.001, tau=0.03)
    rowwise = np.stack([lowpass(row, dt=0.001, tau=0.03) for row in sig], axis=0)
    assert np.allclose(vectorised, rowwise)


def test_lowpass_biquad_vectorised_axis_matches_individual_rows():
    rng = np.random.default_rng(88)
    sig = rng.standard_normal((2, 384))
    vectorised = lowpass_biquad_filtfilt(sig, dt=0.001, tau=0.03)
    rowwise = np.stack(
        [lowpass_biquad_filtfilt(row, dt=0.001, tau=0.03) for row in sig],
        axis=0,
    )
    assert np.allclose(vectorised, rowwise)
