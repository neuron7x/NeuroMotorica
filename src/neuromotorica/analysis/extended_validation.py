from __future__ import annotations
import json
import numpy as np
from ..models.pool import Pool
from ..models.enhanced_nmj import EnhancedNMJParams
from ..models.extended_nmj import ExtendedNMJParams, ExtendedOptimizedNMJ
from ..models.extended_muscle import ExtendedMuscleParams, ExtendedMuscle

def simulate_extended(seconds: float = 1.0, dt: float = 0.001, units: int = 64, rate_hz: float = 10.0,
                      noise_sigma: float = 0.05, glial_gain: float = 0.25, topo_factor: float = 1.2, seed: int = 7) -> dict:
    pool = Pool(units=units, dt=dt, T=seconds)
    spikes = pool.poisson_spikes(rate_hz=rate_hz, seed=seed)
    basep = EnhancedNMJParams(quantal_content=1.2, tau_rise=0.005, tau_decay=0.045, ach_decay=0.025,
                              ach_ratio=0.7, histamine_ratio=0.3, co_transmission=True, modulation_gain=1.2)
    extp = ExtendedNMJParams(**basep.__dict__, noise_sigma=noise_sigma, glial_mod_gain=glial_gain)
    nmj = ExtendedOptimizedNMJ(extp, dt, seconds)
    mp = ExtendedMuscleParams(F_max=1200.0, mu_size_ratio=35.0, tau_act=0.012, tau_deact=0.045, topography_factor=topo_factor)
    muscle = ExtendedMuscle(mp, dt, seconds, units=units)

    act, failure_prob, snr = nmj.extended_activation(spikes)
    F, _ = muscle.force(act)

    return {
        "config": {"seconds": seconds, "dt": dt, "units": units, "rate_hz": rate_hz,
                   "noise_sigma": noise_sigma, "glial_gain": glial_gain, "topography_factor": topo_factor},
        "metrics": {"failure_probability": round(failure_prob, 4), "snr": round(snr, 4),
                    "peak_force_N": float(np.max(F)), "mean_force_N": float(np.mean(F))}
    }

if __name__ == "__main__":
    out = simulate_extended()
    print(json.dumps(out, ensure_ascii=False, indent=2))
