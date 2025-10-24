# SPDX-License-Identifier: Apache-2.0
import json, csv, pathlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import typer
from .runner import BenchRunner, BenchScenario, load_thresholds, Heatmap
from .report import render_html

app = typer.Typer(help="Neuromotorica benchmark suite")

@app.command("run")
def bench(
    scenario: List[str] = typer.Option(["thompson","linucb","egreedy"], "--scenario","-s"),
    data_sizes: List[int] = typer.Option([1000,10000], "--n","-n"),
    profile: str = typer.Option("standard", "--profile","-p"),
    seed: int = typer.Option(42, "--seed"),
    repeats: int = typer.Option(5, "--repeats","-r"),
    outdir: pathlib.Path = typer.Option(pathlib.Path("outputs"), "--outdir"),
    fmt: str = typer.Option("json,csv,html", "--format"),
    baseline: Optional[pathlib.Path] = typer.Option(None, "--baseline"),
    thresholds_path: pathlib.Path = typer.Option(pathlib.Path("benchmarks/thresholds.yml"), "--thresholds"),
    fail_on_regress: bool = typer.Option(True, "--fail-on-regress/--no-fail-on-regress"),
):
    np.random.seed(seed)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = outdir / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    runner = BenchRunner(profile=profile, seed=seed)
    thresholds = load_thresholds(thresholds_path)
    rows: List[Dict[str, Any]] = []
    for sc in scenario:
        scen = runner.get_scenario(sc)
        for n in data_sizes:
            row = runner.measure(scen, n=n, repeats=repeats)
            row.update({"scenario": sc, "n": n, "profile": profile, "seed": seed, "timestamp": ts})
            rows.append(row)
            Heatmap.plot(row["latency_samples"], run_dir / f"{sc}_{n}_heatmap.png", f"{sc} n={n}")
    if "json" in fmt:
        (run_dir/"results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    if "csv" in fmt:
        import csv
        with (run_dir/"results.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=sorted(rows[0].keys())); w.writeheader(); w.writerows(rows)
    cmp_ = runner.compare_with_baseline(rows, baseline, thresholds)
    (run_dir/"compare.json").write_text(json.dumps(cmp_, indent=2), encoding="utf-8")
    if "html" in fmt:
        (run_dir/"report.html").write_text(render_html(rows, cmp_, f"Benchmark {ts}", run_dir), encoding="utf-8")
    fails = [c for c in cmp_["checks"] if c["status"] == "fail"]
    if fail_on_regress and fails:
        raise typer.Exit(code=2)
