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
    r = client.post("/policy/outcome", json={
        "user_id": "u1",
        "exercise_id": "squat",
        "cue_text": "Тримай темп",
        "success": True,
        "profile": "healthy",
    })
    assert r.status_code == 200
    r2 = client.get("/policy/best/u1/squat", params={"k": 3, "profile": "healthy"})
    assert r2.status_code == 200
    payload = r2.json()
    assert payload["user_id"] == "u1"
    assert payload["exercise_id"] == "squat"
    assert isinstance(payload["recommendations"], list)
    assert payload["recommendations"][0]["cue"] == "Тримай темп"

    # Ensure profile-specific filtering keeps namespaces isolated
    r3 = client.get("/policy/best/u1/squat", params={"k": 3, "profile": "post-op"})
    assert r3.status_code == 200
    assert r3.json()["recommendations"] == []
