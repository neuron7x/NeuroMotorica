from __future__ import annotations
import pathlib, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ..models.pool import Pool
from ..models.nmj import NMJ, NMJParams
from ..models.enhanced_nmj import EnhancedNMJ, EnhancedNMJParams, OptimizedEnhancedNMJ
from ..models.muscle import Muscle, MuscleParams

def plot_scenarios(
    outdir: str = "outputs",
    seconds: float = 1.0,
    dt: float = 0.001,
    units: int = 64,
    rate_hz: float = 10.0,
    seed: int = 42,
    fft_threshold: int = 2048,
) -> dict:
    od = pathlib.Path(outdir); od.mkdir(parents=True, exist_ok=True)
    pool = Pool(units=units, dt=dt, T=seconds)
    nmjp = NMJParams()
    enhp = EnhancedNMJParams(quantal_content=1.2, tau_rise=0.005, tau_decay=0.045, ach_decay=0.025,
                             co_transmission=True, ach_ratio=0.7, histamine_ratio=0.3, modulation_gain=1.2)
    mp = MuscleParams(F_max=1200.0, mu_size_ratio=35.0, tau_act=0.012, tau_deact=0.045)
    nmj = NMJ(nmjp, dt, seconds, fft_threshold=fft_threshold)
    enm = EnhancedNMJ(enhp, dt, seconds, fft_threshold=fft_threshold)
    onmj = OptimizedEnhancedNMJ(enhp, dt, seconds, fft_threshold=fft_threshold)
    muscle = Muscle(mp, dt, seconds, units=units)

    idx = int(0.05 / dt)
    spikes_single = pool.single_spike(idx)
    spikes_rand = pool.poisson_spikes(rate_hz=rate_hz, seed=seed)
    spikes_burst = pool.burst(int(0.2/dt), int(0.3/dt), units=units)

    def actF(spikes):
        a0 = nmj.calcium_activation(spikes)
        a1 = enm.dual_transmission_activation(spikes)
        a2 = onmj.physiologically_realistic_activation(spikes)
        Fb, _ = muscle.force(a0)
        Fe, _ = muscle.force(a1)
        Fo, _ = muscle.force(a2)
        return (a0, a1, a2, Fb, Fe, Fo)

    a0s, a1s, a2s, Fb0, Fe0, Fo0 = actF(spikes_single)
    a0r, a1r, a2r, Fb1, Fe1, Fo1 = actF(spikes_rand)
    a0b, a1b, a2b, Fb2, Fe2, Fo2 = actF(spikes_burst)

    t = np.arange(0, int(seconds/dt)) * dt

    def save_plot(x, y_dict, fname: str, xlabel: str, ylabel: str):
        plt.figure()
        for label, y in y_dict.items():
            plt.plot(x, y, label=label)
        plt.xlabel(xlabel); plt.ylabel(ylabel); plt.legend()
        plt.tight_layout()
        p = od / fname
        plt.savefig(p)
        plt.close()
        return str(p)

    files = {}
    files["single_activation.png"] = save_plot(t, {"ACh": a0s.mean(axis=0), "ACh+Hist": a1s.mean(axis=0), "Optimized": a2s.mean(axis=0)}, "single_activation.png", "t, s", "activation")
    files["single_force.png"] = save_plot(t, {"Base": Fb0, "Enhanced": Fe0, "Optimized": Fo0}, "single_force.png", "t, s", "force (N)")
    files["poisson_force.png"] = save_plot(t, {"Base": Fb1, "Enhanced": Fe1, "Optimized": Fo1}, "poisson_force.png", "t, s", "force (N)")
    files["burst_force.png"] = save_plot(t, {"Base": Fb2, "Enhanced": Fe2, "Optimized": Fo2}, "burst_force.png", "t, s", "force (N)")
    return files
