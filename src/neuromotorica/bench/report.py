# SPDX-License-Identifier: Apache-2.0
from pathlib import Path
from typing import List, Dict, Any

def render_html(results: List[Dict[str,Any]], compare: Dict[str,Any], title:str, run_dir:Path)->str:
    import html
    rows = "".join(
        f"<tr><td>{r['scenario']}</td><td>{r['n']}</td><td>{r['profile']}</td>"
        f"<td>{r['latency_ms_p95']:.2f}</td><td>{r['throughput_ops_per_s']:.1f}</td>"
        f"<td>{r['mem_peak_mb']:.2f}</td></tr>"
        for r in results
    )
    checks = "".join(
        f"<li>{c['key']} • {c.get('metric')} → <b style='color:{'crimson' if c['status']=='fail' else 'green'}'>{c['status']}</b>"
        f"{' ('+str(round(c.get('delta_pct',0),1))+'% ≥ '+str(c.get('limit_pct',''))+'%)' if 'delta_pct'in c else ''}</li>"
        for c in compare['checks']
    )
    return f"""<!doctype html><meta charset="utf-8">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
<h1>{html.escape(title)}</h1>
<h2>Summary</h2>
<ul>{checks}</ul>
<h2>Results</h2>
<table border="1" cellpadding="4" cellspacing="0">
<tr><th>scenario</th><th>n</th><th>profile</th><th>p95 ms</th><th>ops/s</th><th>mem MB</th></tr>
{rows}
</table>
<p>Artifacts: <a href="results.json">results.json</a> • <a href="results.csv">results.csv</a> • <a href="compare.json">compare.json</a></p>
"""
