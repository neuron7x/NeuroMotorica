# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import json, pathlib
from datetime import datetime
from typing import Optional
import typer
from .run import ValidationRunner, load_thresholds, render_html_report

app = typer.Typer(help="Validation suite")

@app.command("run")
def validate_cmd(
    profile: str = typer.Option("standard", "--profile","-p"),
    baseline: Optional[pathlib.Path] = typer.Option(None, "--baseline"),
    outdir: pathlib.Path = typer.Option(pathlib.Path("reports"), "--outdir"),
    format_: str = typer.Option("html,json", "--format","-f"),
    verbose: bool = typer.Option(False, "--verbose","-v"),
):
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    run_dir = outdir / ts; run_dir.mkdir(parents=True, exist_ok=True)
    thresholds = load_thresholds(profile)
    runner = ValidationRunner(profile=profile, thresholds=thresholds, verbose=verbose, run_dir=run_dir)
    result = runner.run_all(baseline=baseline)
    if "json" in format_:
        (run_dir/"validation.json").write_text(json.dumps(result.model_dump(), indent=2), encoding="utf-8")
    if "html" in format_:
        (run_dir/"validation.html").write_text(render_html_report(result, f"Validation {ts}", run_dir, verbose), encoding="utf-8")
    if result.has_blocking_failures: raise typer.Exit(code=2)
