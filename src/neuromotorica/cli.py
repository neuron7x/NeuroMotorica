from __future__ import annotations
import json, typer
from typing import List, Optional
from rich import print
from .edge.coach_loop import run_demo as run_demo_impl
from .models.pool import Pool
from .models.nmj import NMJ, NMJParams
from .models.enhanced_nmj import EnhancedNMJ, EnhancedNMJParams
from .models.muscle import Muscle, MuscleParams
from .analysis.validation import scenario_sim, validate_against_benchmarks
from .analysis.benchmarking import benchmark_scenarios

app = typer.Typer(help="NeuroMotorica CLI")

@app.command(name="run-demo")
def run_demo(data: str = typer.Option("sample_data/mock_reps.json", "--data", help="Path to rep events JSON")):
    run_demo_impl(data)

@app.command(name="validate-model")
def validate_model(seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Simulation length seconds"),
                   rate: float = typer.Option(20.0, "--rate", help="Poisson rate Hz"),
                   units: int = typer.Option(64, "--units", help="Motor units")):
    dt = 0.001
    pool = Pool(units=units, dt=dt, T=seconds)
    spikes = pool.poisson_spikes(rate_hz=rate, seed=42)

    nmjp = NMJParams()
    nmj = NMJ(nmjp, dt, seconds)
    base_act = nmj.calcium_activation(spikes)

    enhp = EnhancedNMJParams(quantal_content=1.2, tau_rise=0.005, tau_decay=0.045, ach_decay=0.025,
                             co_transmission=True, ach_ratio=0.7, histamine_ratio=0.3, modulation_gain=1.2)
    enm = EnhancedNMJ(enhp, dt, seconds)
    enh_act = enm.dual_transmission_activation(spikes)

    mp = MuscleParams(F_max=1200.0, mu_size_ratio=35.0)
    muscle = Muscle(mp, dt, seconds, units=units)

    F_base, _ = muscle.force(base_act)
    F_enh, _ = muscle.force(enh_act)
    imp = (float(F_enh.max()) - float(F_base.max())) / max(float(F_base.max()), 1e-6) * 100.0

    res = {"peak_force_base": float(F_base.max()), "peak_force_enhanced": float(F_enh.max()),
           "peak_force_improvement_pct": round(imp, 2), "time_steps": len(F_base)}
    print(res)

@app.command(name="simulate")
def simulate(seconds: float = 1.0, units: int = 64, rate: float = 10.0):
    dt = 0.001
    out = scenario_sim(seconds=seconds, dt=dt, units=units, rate_hz=rate)
    # Validate
    val = validate_against_benchmarks(out, "data/benchmarks/physio_ranges.json")
    res = {"scenarios": out, "validation": val}
    print(json.dumps(res, ensure_ascii=False, indent=2))


@app.command(name="profile")
def profile(
    seconds: Optional[List[float]] = typer.Option(
        None, "--seconds", "-s", min=0.1, help="One or more simulation durations (seconds)."
    ),
    units: Optional[List[int]] = typer.Option(
        None, "--units", "-u", min=4, help="Motor unit counts to benchmark."
    ),
    rate: Optional[List[float]] = typer.Option(
        None, "--rate", "-r", min=1.0, help="Poisson rate values (Hz) to evaluate."
    ),
    dt: float = typer.Option(0.001, "--dt", min=0.0005, help="Simulation timestep (seconds)."),
    repeats: int = typer.Option(1, "--repeats", min=1, help="How many stochastic repeats per configuration."),
    seed: int = typer.Option(42, "--seed", help="Base RNG seed for reproducible benchmarking."),
):
    metrics = benchmark_scenarios(
        seconds=seconds,
        units=units,
        rates=rate,
        dt=dt,
        repeats=repeats,
        seed=seed,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

@app.command(name="plot")
def plot(seconds: float = 1.0, units: int = 64, rate: float = 10.0, outdir: str = "outputs"):
    from .analysis.viz import plot_scenarios
    files = plot_scenarios(outdir=outdir, seconds=seconds, units=units, rate_hz=rate)
    print(json.dumps({"saved": files}, ensure_ascii=False))

@app.command(name="run-api")
def run_api(host: str = "127.0.0.1", port: int = 8000):
    import uvicorn
    uvicorn.run("neuromotorica.cloud.api.main:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()


@app.command(name="simulate-extended")
def simulate_extended_cmd(seconds: float = 1.0, units: int = 64, rate: float = 10.0,
                          noise_sigma: float = 0.05, glial_gain: float = 0.25, topography: float = 1.2):
    from .analysis.extended_validation import simulate_extended
    out = simulate_extended(seconds=seconds, dt=0.001, units=units, rate_hz=rate,
                            noise_sigma=noise_sigma, glial_gain=glial_gain, topo_factor=topography)
    print(json.dumps(out, ensure_ascii=False))
