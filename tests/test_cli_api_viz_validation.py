import json, os, tempfile, pathlib
from typer.testing import CliRunner
from neuromotorica.cli import app
from fastapi.testclient import TestClient
from neuromotorica.cloud.api.main import app as fastapi_app

runner = CliRunner()

def test_cli_simulate_and_validate_ranges():
    result = runner.invoke(app, ["simulate", "--seconds", "0.5", "--units", "32", "--rate", "10"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["validation"]["time_to_peak_in_range"]
    assert data["validation"]["half_relax_in_range"]
    assert data["validation"]["fusion_freq_in_range"]

def test_cli_plot_creates_files():
    with tempfile.TemporaryDirectory() as td:
        result = runner.invoke(app, ["plot", "--seconds", "0.5", "--units", "16", "--rate", "10", "--outdir", td])
        assert result.exit_code == 0
        out = json.loads(result.stdout)
        for _, path in out["saved"].items():
            assert os.path.exists(path)

def test_api_roundtrip():
    client = TestClient(fastapi_app)
    payload = {
        "user_id": "u1",
        "exercise_id": "squat",
        "cue_text": "Тримай темп",
        "success": True,
        "reps": 12,
        "metrics": {"twitch": 0.42, "snr": 18.0},
        "extended": True,
    }
    r = client.post("/policy/outcome", json=payload)
    assert r.status_code == 200
    out = r.json()
    assert out["status"] == "ok"
    assert out["outcome"]["reps"] == payload["reps"]
    assert out["outcome"]["metrics"] == payload["metrics"]
    assert out["outcome"]["extended"] is True
    assert out["outcome"]["success"] == 1
    r2 = client.get("/policy/best/u1/squat?k=3")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
