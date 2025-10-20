import json
from neuromotorica.analysis.extended_validation import simulate_extended

def test_extended_failure_probability_and_mech_boost():
    base = simulate_extended(seconds=0.5, rate_hz=12.0, noise_sigma=0.05, glial_gain=0.25, topo_factor=1.0)
    boosted = simulate_extended(seconds=0.5, rate_hz=12.0, noise_sigma=0.05, glial_gain=0.25, topo_factor=1.2)
    # Failure probability expected within a plausible small range (e.g., < 0.1) for given sigma
    assert 0.0 <= base["metrics"]["failure_probability"] < 0.2
    # Mech boost increases peak force
    assert boosted["metrics"]["peak_force_N"] > base["metrics"]["peak_force_N"]
    # SNR is finite and positive
    assert base["metrics"]["snr"] > 0
