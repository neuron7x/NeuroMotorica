import numpy as np
import pytest

from neuromotorica_universal.core.nmj import NMJ, SimulationMetrics


def test_nmj_step_and_metrics_basic() -> None:
    nmj = NMJ(dt=0.01, tau=0.1, gain=2.0, noise=0.0)
    u = np.zeros(100)
    u[10:60] = 1.0
    y = nmj.simulate(u)
    metrics = nmj.metrics()

    assert y.max() <= 1.0 and y.min() >= 0.0
    assert metrics.range_of_motion > 0.5
    assert metrics.peak_force > 0.5
    assert metrics.reps >= 1
    assert metrics.tempo > 0


def test_nmj_metrics_empty_history_returns_zeroes() -> None:
    nmj = NMJ()

    metrics = nmj.metrics()

    assert metrics == SimulationMetrics(reps=0, tempo=0.0, range_of_motion=0.0, peak_force=0.0)


def test_nmj_noise_branch_clamps_output() -> None:
    nmj = NMJ(noise=0.2)
    np.random.seed(42)

    value = nmj.step(1.0)

    assert 0.0 <= value <= 1.0


def test_nmj_invalid_parameters_raise() -> None:
    with pytest.raises(ValueError):
        NMJ(dt=0.0)
    with pytest.raises(ValueError):
        NMJ(tau=0.0)
    with pytest.raises(ValueError):
        NMJ(gain=0.0)
    with pytest.raises(ValueError):
        NMJ(noise=-0.1)
