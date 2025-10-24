# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import json, pathlib
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from .validators.openapi import validate_openapi
from .validators.configs import validate_configs
from .validators.policies import validate_policies
from .validators.dataq import validate_data_quality
from .viz import charts_section

class Finding(BaseModel):
    code: str; severity: str; message: str; advice: str = ""; context: Dict[str, Any] = {}

class SectionResult(BaseModel):
    name: str; findings: List[Finding] = []; metrics: Dict[str, Any] = {}

class ValidationResult(BaseModel):
    profile: str; sections: List[SectionResult]; summary: Dict[str, Any]
    has_blocking_failures: bool = Field(default=False)

def load_thresholds(profile: str)->Dict[str,Any]:
    import yaml
    p = pathlib.Path("validations/thresholds.yml")
    if p.exists(): conf = yaml.safe_load(p.read_text()) or {}
    else: conf = {"_default":{"openapi":{"breaking_changes":0},"configs":{"missing_required":0},"policies":{"invalid_files":0},"data":{"schema_errors":0}}}
    return conf.get(profile, conf.get("_default", {}))

class ValidationRunner:
    def __init__(self, profile: str, thresholds: Dict[str,Any], verbose: bool, run_dir: pathlib.Path):
        self.profile=profile; self.thresholds=thresholds; self.verbose=verbose; self.run_dir=run_dir
    def run_all(self, baseline: Optional[pathlib.Path]):
        sections = [
            validate_openapi(self.thresholds, self.run_dir),
            validate_configs(self.thresholds, self.run_dir),
            validate_policies(self.thresholds, self.run_dir),
            validate_data_quality(self.thresholds, self.run_dir),
        ]
        fails = [f for s in sections for f in s.findings if f.severity=="fail"]
        summary = {"total": sum(len(s.findings) for s in sections),
                   "fails": len(fails),
                   "warns": sum(1 for s in sections for f in s.findings if f.severity=="warn")}
        (self.run_dir/"charts.html").write_text(charts_section(sections), encoding="utf-8")
        from pydantic import BaseModel
        class Obj(BaseModel): pass
        return ValidationResult(profile=self.profile, sections=sections, summary=summary, has_blocking_failures=bool(fails))

def render_html_report(result: ValidationResult, title: str, run_dir: pathlib.Path, verbose: bool)->str:
    import html
    rows=[]
    for s in result.sections:
        findings = "".join(f"<li><code>{html.escape(f.code)}</code> <b style='color:{'crimson' if f.severity=='fail' else 'orange' if f.severity=='warn' else 'inherit'}'>{html.escape(f.severity)}</b> — {html.escape(f.message)}<br/><i>Advice:</i> {html.escape(f.advice)}</li>" for f in s.findings)
        metrics = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k,v in s.metrics.items())
        rows.append(f"<h2>{html.escape(s.name)}</h2><ul>{findings}</ul><h4>Metrics</h4><ul>{metrics}</ul>")
    charts=(run_dir/'charts.html').read_text(encoding='utf-8') if (run_dir/'charts.html').exists() else ""
    return f"""<!doctype html><meta charset="utf-8"><title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
<h1>{html.escape(title)}</h1>
<p><b>Profile:</b> {html.escape(result.profile)} | <b>Total:</b> {result.summary['total']} | <b>Fails:</b> {result.summary['fails']} | <b>Warns:</b> {result.summary['warns']}</p>
{charts}
{''.join(rows)}
"""
