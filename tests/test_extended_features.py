from neuromotorica.analysis.extended_validation import simulate_extended


def test_extended_metrics_presence_and_plausibility():
    base = simulate_extended(seconds=0.5, rate_hz=12.0, noise_sigma=0.05, glial_gain=0.25, topo_factor=1.0)
    metrics = base["metrics"]

    assert 0.0 <= metrics["failure_rate"] <= 1.0
    assert metrics["snr"] > 0
    assert metrics["jitter_ms"] >= 0
    assert metrics["latency_cv"] >= 0
    assert metrics["cv_force"] >= 0
    assert metrics["peak_force_N"] >= metrics["mean_force_N"] >= 0


def test_topography_and_failure_bias_effects():
    base = simulate_extended(seconds=0.5, rate_hz=12.0, noise_sigma=0.05, glial_gain=0.25, topo_factor=1.0)
    boosted = simulate_extended(seconds=0.5, rate_hz=12.0, noise_sigma=0.05, glial_gain=0.25, topo_factor=1.2)
    biased = simulate_extended(seconds=0.5, rate_hz=12.0, noise_sigma=0.05, glial_gain=0.25,
                               topo_factor=1.0, failure_bias=0.6)

    assert boosted["metrics"]["peak_force_N"] > base["metrics"]["peak_force_N"]
    assert biased["metrics"]["failure_rate"] >= base["metrics"]["failure_rate"]
    # High failure bias should reduce SNR or increase jitter relative to baseline
    assert biased["metrics"]["snr"] <= base["metrics"]["snr"] or biased["metrics"]["jitter_ms"] >= base["metrics"]["jitter_ms"]
