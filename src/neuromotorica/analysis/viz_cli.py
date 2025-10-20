from __future__ import annotations
import typer, json
from .viz import plot_scenarios

def main(outdir: str = "outputs", seconds: float = 1.0, units: int = 64, rate: float = 10.0):
    files = plot_scenarios(outdir=outdir, seconds=seconds, units=units, rate_hz=rate)
    print(json.dumps({"saved": files}, ensure_ascii=False))

if __name__ == "__main__":
    import sys
    outdir = sys.argv[sys.argv.index("--outdir")+1] if "--outdir" in sys.argv else "outputs"
    main(outdir=outdir)
