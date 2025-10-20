from __future__ import annotations
import json
import numpy as np
from ..models.pool import Pool
from ..models.extended_nmj import ExtendedNMJParams, ExtendedOptimizedNMJ
from ..models.extended_muscle import ExtendedMuscleParams, ExtendedMuscle
from ..profiles import extended_param_dicts

def simulate_extended(seconds: float = 1.0, dt: float = 0.001, units: int = 64, rate_hz: float = 10.0,
                      noise_sigma: float = 0.05, glial_gain: float = 0.25, topo_factor: float = 1.2,
                      seed: int = 7, profile: str = "baseline") -> dict:
    pool = Pool(units=units, dt=dt, T=seconds)
    spikes = pool.poisson_spikes(rate_hz=rate_hz, seed=seed)
    enh_dict, muscle_dict = extended_param_dicts(profile)
    ext_nmj = ExtendedNMJParams(**{**enh_dict, "noise_sigma": noise_sigma, "glial_mod_gain": glial_gain})
    nmj = ExtendedOptimizedNMJ(ext_nmj, dt, seconds)
    ext_muscle = ExtendedMuscleParams(**{**muscle_dict, "topography_factor": topo_factor})
    muscle = ExtendedMuscle(ext_muscle, dt, seconds, units=units)

    act, failure_prob, snr = nmj.extended_activation(spikes)
    F, _ = muscle.force(act)

    return {
        "config": {
            "seconds": seconds,
            "dt": dt,
            "units": units,
            "rate_hz": rate_hz,
            "noise_sigma": noise_sigma,
            "glial_gain": glial_gain,
            "topography_factor": topo_factor,
            "profile": profile,
        },
        "metrics": {"failure_probability": round(failure_prob, 4), "snr": round(snr, 4),
                    "peak_force_N": float(np.max(F)), "mean_force_N": float(np.mean(F))}
    }

if __name__ == "__main__":
    out = simulate_extended()
    print(json.dumps(out, ensure_ascii=False, indent=2))
