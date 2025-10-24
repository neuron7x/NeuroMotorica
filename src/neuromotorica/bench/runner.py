# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import time, tracemalloc, json, pathlib
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np, yaml, importlib

@dataclass
class BenchScenario:
    name: str
    fn: str
    def load(self):
        mod, func = self.fn.split(":")
        return getattr(importlib.import_module(mod), func)

class BenchRunner:
    def __init__(self, profile: str, seed: int):
        self.profile = profile; self.seed = seed
        self.registry = {
            "thompson": BenchScenario("thompson", "neuromotorica.algo.bandits:bench_thompson"),
            "linucb":   BenchScenario("linucb",   "neuromotorica.algo.bandits:bench_linucb"),
            "egreedy":  BenchScenario("egreedy",  "neuromotorica.algo.bandits:bench_egreedy"),
        }
    def get_scenario(self, name: str)->BenchScenario:
        if name not in self.registry: raise ValueError(f"Unknown scenario: {name}")
        return self.registry[name]
    def measure(self, scen: BenchScenario, n:int, repeats:int)->Dict[str,Any]:
        fn = scen.load()
        lat, mem, ops_total = [], [], 0
        for _ in range(repeats):
            tracemalloc.start()
            t0 = time.perf_counter()
            ops = fn(n=n, seed=self.seed, profile=self.profile)
            dt = time.perf_counter() - t0
            peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
            lat.append(dt*1000.0); mem.append(peak/(1024*1024)); ops_total += ops
        import numpy as np
        return {
            "latency_ms_avg": float(np.mean(lat)),
            "latency_ms_p95": float(np.percentile(lat, 95)),
            "throughput_ops_per_s": float(ops_total / (sum(lat)/1000.0) if sum(lat)>0 else 0.0),
            "mem_peak_mb": float(max(mem) if mem else 0.0),
            "latency_samples": [float(x) for x in lat],
            "mem_samples_mb": [float(x) for x in mem],
            "repeats": repeats,
        }
    def compare_with_baseline(self, current, baseline_path: Optional[pathlib.Path], thresholds: Dict[str,Any]):
        base = {}
        paths = []
        if baseline_path and baseline_path.exists():
            paths = [baseline_path] if baseline_path.is_file() else list(baseline_path.glob("*.json"))
        else:
            paths = list(pathlib.Path("benchmarks/baseline").glob("*.json"))
        for p in paths:
            try:
                for r in json.loads(p.read_text()):
                    base[(r["scenario"], r["n"], r["profile"])] = r
            except Exception:
                pass
        checks=[]
        for row in current:
            key=(row["scenario"], row["n"], row["profile"])
            if key not in base:
                checks.append({"key": key, "metric":"baseline_missing","status":"warn"}); continue
            th = thresholds.get(row["scenario"], thresholds.get("_default", {}))
            for metric in ["latency_ms_p95","latency_ms_avg","mem_peak_mb"]:
                limit = th.get(metric, {}).get("max_regression_pct", 30.0)
                cur, old = row[metric], base[key][metric]
                pct = 0.0 if old==0 else ((cur-old)/old)*100.0
                checks.append({"key":key,"metric":metric,"baseline":old,"current":cur,"delta_pct":pct,"limit_pct":limit,"status":"pass" if pct<=limit else "fail"})
        return {"checks": checks}

def load_thresholds(path: pathlib.Path)->Dict[str,Any]:
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {"_default":{"latency_ms_p95":{"max_regression_pct":30},"latency_ms_avg":{"max_regression_pct":30},"mem_peak_mb":{"max_regression_pct":20}}}

class Heatmap:
    @staticmethod
    def plot(samples_ms, outpath, title):
        import matplotlib.pyplot as plt, numpy as np
        arr = np.array([samples_ms])
        plt.figure(); plt.imshow(arr, aspect="auto"); plt.title(title); plt.xlabel("repeat"); plt.ylabel("latency ms"); plt.colorbar(label="ms")
        plt.savefig(outpath, dpi=120, bbox_inches="tight"); plt.close()
