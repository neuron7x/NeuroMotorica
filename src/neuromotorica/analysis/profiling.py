"""Profiling utilities for NeuroMotorica simulations."""

from __future__ import annotations

import statistics
from time import perf_counter
from typing import Any, Dict, List

from .validation import scenario_sim


def _summary_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"mean": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": round(statistics.fmean(values), 6),
        "stdev": round(statistics.pstdev(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def profile_simulation(
    *,
    seconds: float,
    dt: float,
    units: int,
    rate_hz: float,
    repeats: int,
    profile: str,
    fft_threshold: int | None,
    seed: int,
) -> Dict[str, Any]:
    """Profile repeated simulation runs and surface optimisation hints."""

    runtimes: List[float] = []
    force_improvements: List[float] = []
    snr_gains: List[float] = []
    seeds = [seed + idx for idx in range(repeats)]

    for idx, run_seed in enumerate(seeds):
        t0 = perf_counter()
        result = scenario_sim(
            seconds=seconds,
            dt=dt,
            units=units,
            rate_hz=rate_hz,
            seed=run_seed,
            profile=profile,
            fft_threshold=fft_threshold,
        )
        runtimes.append(result["runtime"]["single_spike_sec"])
        poisson_forces = result["random_poisson"]["forces_N"]
        baseline_force = float(poisson_forces["baseline"]) or 1e-9
        optimized_force = float(poisson_forces["optimized"])
        force_improvements.append((optimized_force - baseline_force) / baseline_force * 100.0)
        snr_metrics = result["random_poisson"]["snr"]
        snr_gains.append(float(snr_metrics["optimized"]) - float(snr_metrics["baseline"]))
        runtimes[-1] = max(runtimes[-1], perf_counter() - t0)

    runtime_stats = _summary_stats([r * 1000.0 for r in runtimes])
    improvement_stats = _summary_stats(force_improvements)
    snr_stats = _summary_stats(snr_gains)

    recommendations: List[Dict[str, str]] = []
    if runtime_stats["mean"] > 40.0 and (fft_threshold is None or fft_threshold > 1024):
        recommendations.append(
            {
                "type": "performance",
                "suggestion": "Lower the FFT threshold (e.g. 1024) to accelerate convolutions.",
            }
        )
    if improvement_stats["mean"] < 5.0:
        recommendations.append(
            {
                "type": "signal",
                "suggestion": "Increase quantal_content or modulation_gain in the selected profile for stronger force gains.",
            }
        )
    if snr_stats["mean"] < 0.5:
        recommendations.append(
            {
                "type": "robustness",
                "suggestion": "Boost histamine_ratio or reduce noise inputs to improve activation SNR.",
            }
        )

    return {
        "config": {
            "seconds": seconds,
            "dt": dt,
            "units": units,
            "rate_hz": rate_hz,
            "repeats": repeats,
            "profile": profile,
            "fft_threshold": fft_threshold,
            "seed": seed,
        },
        "metrics": {
            "runtime_ms": runtime_stats,
            "force_improvement_pct": improvement_stats,
            "snr_gain": snr_stats,
        },
        "recommendations": recommendations,
    }
