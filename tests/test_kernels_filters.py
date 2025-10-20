import numpy as np
from neuromotorica.models.kernels import alpha_kernel, normalized_alpha_kernel, convolve_signal
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
    k = normalized_alpha_kernel(np.linspace(0,0.5,500), 0.005, 0.05)
    d = np.convolve(sig, k, mode="full")[: len(sig)]
    f = convolve_signal(sig, k, use_fft_threshold=256)
    rmse = np.sqrt(np.mean((d - f)**2))
    assert rmse < 1e-9
