import numpy as np
from neuromotorica.models.nmj import NMJ, NMJParams
from neuromotorica.models.enhanced_nmj import EnhancedNMJ, EnhancedNMJParams, OptimizedEnhancedNMJ
from neuromotorica.models.pool import Pool
from neuromotorica.models.muscle import Muscle, MuscleParams

def test_nmj_enhanced_shapes_and_bounds():
    dt, T = 0.001, 0.5
    pool = Pool(units=16, dt=dt, T=T)
    spikes = pool.poisson_spikes(rate_hz=20, seed=1)

    base = NMJ(NMJParams(), dt, T)
    enh = EnhancedNMJ(EnhancedNMJParams(), dt, T)
    opt = OptimizedEnhancedNMJ(EnhancedNMJParams(), dt, T)

    a0 = base.calcium_activation(spikes)
    a1 = enh.dual_transmission_activation(spikes)
    a2 = opt.physiologically_realistic_activation(spikes)

    assert a0.shape == spikes.shape and a1.shape == spikes.shape and a2.shape == spikes.shape
    assert 0.0 <= a0.min() <= 1.0 and a0.max() <= 1.0
    assert 0.0 <= a1.min() <= 1.5 and a1.max() <= 1.5
    assert 0.0 <= a2.min() <= 1.2 and a2.max() <= 1.2
    assert a1.mean() >= a0.mean()

def test_muscle_force_and_passive():
    dt, T = 0.001, 0.5
    pool = Pool(units=8, dt=dt, T=T)
    spikes = pool.burst(100, 200)
    base = NMJ(NMJParams(), dt, T)
    act = base.calcium_activation(spikes)
    muscle = Muscle(MuscleParams(), dt, T, units=pool.units)
    F1, _ = muscle.force(act, L=1.0, V=0.0)
    F2, _ = muscle.force(act, L=1.2, V=0.0)
    assert F1.max() > 0 and F2.max() > F1.max()
