\
import numpy as np
from neuromotorica_universal.core.nmj import NMJ

def test_nmj_step_and_metrics_basic():
    nmj = NMJ(dt=0.01, tau=0.1, gain=2.0, noise=0.0)
    u = np.zeros(100)
    u[10:60] = 1.0
    y = nmj.simulate(u)
    m = nmj.metrics()
    assert y.max() <= 1.0 and y.min() >= 0.0
    assert m.range_of_motion > 0.5
    assert m.peak_force > 0.5
    assert m.reps >= 1
    assert m.tempo > 0
