from __future__ import annotations
import json, pathlib
from .validation import scenario_sim, validate_against_benchmarks

def main():
    res = scenario_sim(seconds=1.0, dt=0.001, units=64, rate_hz=10.0)
    val = validate_against_benchmarks(res, str(pathlib.Path(__file__).parents[2] / "data/benchmarks/physio_ranges.json"))
    print(json.dumps({"result": res, "validation": val}, ensure_ascii=False))

if __name__ == "__main__":
    main()
