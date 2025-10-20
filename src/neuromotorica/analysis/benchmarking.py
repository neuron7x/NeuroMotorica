"""Benchmark utilities for profiling NeuroMotorica simulations.

The helper below reuses :func:`scenario_sim` to keep metric
calculations consistent with the rest of the validation pipeline.
It wraps execution timing, computes throughput-style indicators and
derives lightweight heuristics for suggesting parameter tweaks. The
goal is to provide a structured artefact that can feed dashboards or
CI alerts without baking policy decisions into the CLI surface.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import product
from statistics import mean, median
from time import perf_counter
from typing import List, Sequence

from .validation import scenario_sim


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for a single simulation benchmark."""

    seconds: float
    dt: float
    units: int
    rate_hz: float
    repeat: int


def _relative_pct(delta: float, reference: float) -> float:
    denom = max(abs(reference), 1e-9)
    return (delta / denom) * 100.0


def _force_deltas(force_block: dict) -> dict:
    baseline = float(force_block["baseline"])
    enhanced = float(force_block["enhanced"])
    optimized = float(force_block["optimized"])
    return {
        "optimized_vs_baseline_pct": round(_relative_pct(optimized - baseline, baseline), 3),
        "optimized_vs_enhanced_pct": round(_relative_pct(optimized - enhanced, enhanced), 3),
        "enhanced_vs_baseline_pct": round(_relative_pct(enhanced - baseline, baseline), 3),
    }


def _snr_gain(snr_block: dict) -> dict:
    baseline = float(snr_block["baseline"])
    enhanced = float(snr_block["enhanced"])
    optimized = float(snr_block["optimized"])
    return {
        "baseline": round(baseline, 4),
        "enhanced": round(enhanced, 4),
        "optimized": round(optimized, 4),
        "gain_vs_baseline": round(optimized - baseline, 4),
        "gain_vs_enhanced": round(optimized - enhanced, 4),
    }


def _suggest_tweaks(throughput: dict, force_error: dict, snr: dict, config: BenchmarkConfig) -> List[str]:
    suggestions: List[str] = []

    if throughput["activations_per_sec"] < 5e5:
        target_dt = min(config.dt * 2.0, 0.004)
        reduced_units = max(config.units - 8, max(config.units // 2, 8))
        suggestions.append(
            "Increase dt (e.g., to {:.3f} s) or reduce motor units to ≤{} to boost kernel throughput.".format(
                target_dt, reduced_units
            )
        )

    if abs(force_error["optimized_vs_enhanced_pct"]) > 5.0:
        suggestions.append(
            "Retune EnhancedNMJ quantal_content or modulation_gain to align optimized vs enhanced forces."
        )

    if snr["gain_vs_baseline"] < 0.2:
        suggestions.append(
            "Raise stimulation rate or add motor units to improve activation SNR."
        )

    if not suggestions:
        suggestions.append("Parameters within recommended envelopes; no tweaks required.")

    return suggestions


def _normalize_sequence(values: Sequence[float] | None, fallback: float) -> List[float]:
    if not values:
        return [fallback]
    return list(dict.fromkeys(values))


def benchmark_scenarios(
    seconds: Sequence[float] | None = None,
    units: Sequence[int] | None = None,
    rates: Sequence[float] | None = None,
    *,
    dt: float = 0.001,
    repeats: int = 1,
    seed: int = 42,
) -> dict:
    """Run a sweep of simulation scenarios and return structured metrics."""

    seconds_list = _normalize_sequence(seconds, 0.5)
    units_list = _normalize_sequence(units, 32)
    rates_list = _normalize_sequence(rates, 10.0)
    repeats = max(int(repeats), 1)

    results = []

    for (sec, unit, rate), rep in product(
        product(seconds_list, units_list, rates_list), range(repeats)
    ):
        config = BenchmarkConfig(seconds=sec, dt=dt, units=unit, rate_hz=rate, repeat=rep)
        start = perf_counter()
        scenario = scenario_sim(seconds=sec, dt=dt, units=unit, rate_hz=rate, seed=seed + rep)
        wall = perf_counter() - start

        total_steps = max(int(round(sec / dt)), 1)
        activations = total_steps * unit
        wall_clamped = max(wall, 1e-9)

        throughput = {
            "time_steps": total_steps,
            "units": unit,
            "steps_per_second": round(total_steps / wall_clamped, 2),
            "activations_per_sec": round(activations / wall_clamped, 2),
        }

        random_forces = scenario["random_poisson"]["forces_N"]
        force_error = _force_deltas(random_forces)
        snr_gain = _snr_gain(scenario["random_poisson"]["snr"])
        tweaks = _suggest_tweaks(throughput, force_error, snr_gain, config)

        results.append(
            {
                "config": {
                    "seconds": round(sec, 4),
                    "dt": round(dt, 4),
                    "units": unit,
                    "rate_hz": round(rate, 3),
                    "repeat": rep,
                },
                "timing": {
                    "wall_time_sec": round(wall, 4),
                    "single_spike_kernel_sec": scenario["runtime"]["single_spike_sec"],
                },
                "kernel_throughput": throughput,
                "force_error_pct": force_error,
                "snr": snr_gain,
                "suggested_tweaks": tweaks,
            }
        )

    if not results:
        return {"benchmarks": [], "summary": {}}

    wall_times = [item["timing"]["wall_time_sec"] for item in results]
    throughputs = [item["kernel_throughput"]["activations_per_sec"] for item in results]
    force_errors = [abs(item["force_error_pct"]["optimized_vs_enhanced_pct"]) for item in results]
    snr_gains = [item["snr"]["gain_vs_baseline"] for item in results]

    suggestion_counter: Counter[str] = Counter()
    for item in results:
        suggestion_counter.update(item["suggested_tweaks"])

    summary = {
        "scenario_count": len(results),
        "average_wall_time_sec": round(mean(wall_times), 4),
        "median_force_error_abs_pct": round(median(force_errors), 3),
        "throughput_activations_per_sec": {
            "min": round(min(throughputs), 2),
            "max": round(max(throughputs), 2),
            "median": round(median(throughputs), 2),
        },
        "snr_gain_vs_baseline": {
            "min": round(min(snr_gains), 4),
            "max": round(max(snr_gains), 4),
            "median": round(median(snr_gains), 4),
        },
        "recommendations": [
            {"suggestion": text, "count": count}
            for text, count in suggestion_counter.most_common()
        ],
    }

    return {"benchmarks": results, "summary": summary}

