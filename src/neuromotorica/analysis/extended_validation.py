from __future__ import annotations
import json
import numpy as np
from ..models.pool import Pool
from ..models.extended_nmj import ExtendedNMJParams, ExtendedOptimizedNMJ
from ..models.extended_muscle import ExtendedMuscleParams, ExtendedMuscle
from ..profiles import extended_param_dicts

def simulate_extended(
    seconds: float = 1.0,
    dt: float = 0.001,
    units: int = 64,
    rate_hz: float = 10.0,
    noise_sigma: float = 0.05,
    glial_gain: float = 0.25,
    topo_factor: float = 1.2,
    failure_bias: float = 0.0,
    seed: int = 7,
    profile: str = "baseline",
    fft_threshold: int | None = None,
) -> dict:
    pool = Pool(units=units, dt=dt, T=seconds)
    spikes = pool.poisson_spikes(rate_hz=rate_hz, seed=seed)
    enh_dict, muscle_dict = extended_param_dicts(profile)
    ext_nmj = ExtendedNMJParams(
        **{**enh_dict, "noise_sigma": noise_sigma, "glial_mod_gain": glial_gain, "failure_bias": failure_bias}
    )
    nmj = ExtendedOptimizedNMJ(ext_nmj, dt, seconds, fft_threshold=fft_threshold)
    ext_muscle = ExtendedMuscleParams(**{**muscle_dict, "topography_factor": topo_factor})
    muscle = ExtendedMuscle(ext_muscle, dt, seconds, units=units)

    act, failure_rate, snr, jitter_ms = nmj.extended_activation(
        spikes,
        failure_bias=failure_bias,
        fft_threshold=fft_threshold,
    )
    F, _ = muscle.force(act)
    mean_force = float(np.mean(F))
    cv_force = float((np.std(F) / max(mean_force, 1e-9)))

    return {
        "config": {
            "seconds": seconds,
            "dt": dt,
            "units": units,
            "rate_hz": rate_hz,
            "noise_sigma": noise_sigma,
            "glial_gain": glial_gain,
            "topography_factor": topo_factor,
            "failure_bias": failure_bias,
            "profile": profile,
            "fft_threshold": fft_threshold,
        },
        "metrics": {
            "failure_rate": round(failure_rate, 4),
            "failure_probability": round(failure_rate, 4),
            "snr": round(snr, 4),
            "jitter_ms": round(jitter_ms, 3),
            "peak_force_N": float(np.max(F)),
            "mean_force_N": mean_force,
            "cv_force": round(cv_force, 4),
        },
    }

if __name__ == "__main__":
    out = simulate_extended()
    print(json.dumps(out, ensure_ascii=False, indent=2))
