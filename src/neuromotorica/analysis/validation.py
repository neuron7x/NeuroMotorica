from __future__ import annotations
import time, json, pathlib
import numpy as np
from numpy.typing import NDArray
from ..models.nmj import NMJ
from ..models.enhanced_nmj import EnhancedNMJ, OptimizedEnhancedNMJ
from ..models.muscle import Muscle
from ..profiles import build_profile_params
from ..models.pool import Pool

def twitch_metrics(force: NDArray[np.float64], dt: float, window_s: float = 0.3) -> dict:
    Tn = len(force)
    win = min(Tn, int(window_s / dt))
    seg = force[:win]
    baseline = float(seg[0])
    peak = float(np.max(seg))
    diffs = np.diff(seg)
    slope_idx = int(np.argmax(diffs)) if diffs.size else 0
    rise_threshold = baseline + 0.1 * (peak - baseline)
    threshold_idx = 0
    if rise_threshold > baseline:
        candidates = np.flatnonzero(seg >= rise_threshold)
        if candidates.size:
            threshold_idx = int(candidates[0])
    onset_idx = max(slope_idx, threshold_idx)
    ttp_idx = int(np.argmax(seg))
    ttp = max(ttp_idx - onset_idx, 0) * dt * 1000.0
    peak = float(np.max(seg))
    half = peak / 2.0
    post = seg[ttp_idx:]
    if len(post) > 1:
        hr_rel_idx = ttp_idx + int(np.argmin(np.abs(post - half)))
        half_rel = (hr_rel_idx - ttp_idx) * dt * 1000.0
    else:
        half_rel = 0.0
    contr_vel = peak / max(ttp / 1000.0, 1e-9)
    return {"time_to_peak_ms": round(ttp, 2), "half_relaxation_time_ms": round(half_rel, 2),
            "peak_force_N": round(peak, 3), "contraction_velocity_Ns": round(contr_vel, 3)}

def scenario_sim(
    seconds: float = 1.0,
    dt: float = 0.001,
    units: int = 64,
    rate_hz: float = 10.0,
    seed: int = 42,
    profile: str = "baseline",
    fft_threshold: int | None = None,
) -> dict:
    pool = Pool(units=units, dt=dt, T=seconds)
    nmjp, enhp, mp, meta = build_profile_params(profile)
    nmj = NMJ(nmjp, dt, seconds, fft_threshold=fft_threshold)
    enm = EnhancedNMJ(enhp, dt, seconds, fft_threshold=fft_threshold)
    onmj = OptimizedEnhancedNMJ(enhp, dt, seconds, fft_threshold=fft_threshold)
    muscle = Muscle(mp, dt, seconds, units=units)
    idx = int(0.05 / dt)
    single = pool.single_spike(idx)
    burst = pool.burst(int(0.2/dt), int(0.3/dt), units=units)
    rand = pool.poisson_spikes(rate_hz=rate_hz, seed=seed)

    def run(spikes: NDArray[np.float64]):
        base = nmj.calcium_activation(spikes)
        enh = enm.dual_transmission_activation(spikes)
        opt = onmj.physiologically_realistic_activation(spikes)
        Fb, _ = muscle.force(base)
        Fe, _ = muscle.force(enh)
        Fo, _ = muscle.force(opt)
        return (base, enh, opt, Fb, Fe, Fo)

    t0 = time.time()
    b0, e0, o0, Fb0, Fe0, Fo0 = run(single)
    single_runtime = time.time() - t0

    b1, e1, o1, Fb1, Fe1, Fo1 = run(rand)
    b2, e2, o2, Fb2, Fe2, Fo2 = run(burst)

    def snr(act: NDArray[np.float64]) -> float:
        m = float(np.mean(act))
        s = float(np.std(act)) or 1e-9
        return m / s

    fusion_freq = 1.0 / (mp.tau_act + mp.tau_deact)

    return {
        "config": {
            "seconds": seconds,
            "dt": dt,
            "units": units,
            "rate_hz": rate_hz,
            "profile": profile,
            "profile_description": meta.get("description", ""),
            "fft_threshold": fft_threshold,
        },
        "runtime": {"single_spike_sec": round(single_runtime, 4)},
        "single_spike": {"twitch": twitch_metrics(Fo0, dt), "fusion_frequency_Hz": round(fusion_freq, 3),
                         "forces_N": {"baseline": float(np.max(Fb0)), "enhanced": float(np.max(Fe0)), "optimized": float(np.max(Fo0))}},
        "random_poisson": {"forces_N": {"baseline": float(np.max(Fb1)), "enhanced": float(np.max(Fe1)), "optimized": float(np.max(Fo1))},
                           "snr": {"baseline": round(snr(b1), 4), "enhanced": round(snr(e1), 4), "optimized": round(snr(o1), 4)}},
        "burst": {"forces_N": {"baseline": float(np.max(Fb2)), "enhanced": float(np.max(Fe2)), "optimized": float(np.max(Fo2))},
                  "summation_efficiency": round(float(np.mean(Fo2)) / max(float(np.mean(Fb2)), 1e-9), 3)},
    }

def validate_against_benchmarks(result: dict, bench_path: str) -> dict:
    data = json.loads(pathlib.Path(bench_path).read_text(encoding="utf-8"))
    ok_ranges = {}
    tw = result["single_spike"]["twitch"]
    ttp_ok = data["twitch"]["time_to_peak_ms"][0] <= tw["time_to_peak_ms"] <= data["twitch"]["time_to_peak_ms"][1]
    hr_ok = data["twitch"]["half_relaxation_time_ms"][0] <= tw["half_relaxation_time_ms"] <= data["twitch"]["half_relaxation_time_ms"][1]
    ff = result["single_spike"]["fusion_frequency_Hz"]
    ff_ok = data["fusion_frequency_Hz"][0] <= ff <= data["fusion_frequency_Hz"][1]
    return {"time_to_peak_in_range": ttp_ok, "half_relax_in_range": hr_ok, "fusion_freq_in_range": ff_ok}
