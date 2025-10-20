import json, os, tempfile, pathlib
import pytest
from typer.testing import CliRunner
from neuromotorica.cli import app
from neuromotorica.profiles import available_profiles
from fastapi.testclient import TestClient
from neuromotorica.cloud.api.main import app as fastapi_app

runner = CliRunner()

@pytest.mark.parametrize("profile", available_profiles())
def test_cli_simulate_and_validate_ranges(profile):
    result = runner.invoke(app, [
        "simulate", "--seconds", "0.5", "--units", "32", "--rate", "10", "--profile", profile
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["scenarios"]["config"]["profile"] == profile
    assert data["validation"]["time_to_peak_in_range"]
    assert data["validation"]["half_relax_in_range"]
    assert data["validation"]["fusion_freq_in_range"]

def test_cli_plot_creates_files():
    with tempfile.TemporaryDirectory() as td:
        profile = available_profiles()[1]
        result = runner.invoke(app, [
            "plot", "--seconds", "0.5", "--units", "16", "--rate", "10", "--outdir", td,
            "--profile", profile
        ])
        assert result.exit_code == 0
        out = json.loads(result.stdout)
        for _, path in out["saved"].items():
            assert os.path.exists(path)


def test_cli_rejects_unknown_profile():
    result = runner.invoke(app, ["simulate", "--profile", "unknown-profile"])
    assert result.exit_code != 0
    assert "Unknown profile" in result.stdout

def test_api_roundtrip():
    client = TestClient(fastapi_app)
    r = client.post("/policy/outcome", json={
        "user_id": "u1", "exercise_id": "squat", "cue_text": "Тримай темп", "success": True
    })
    assert r.status_code == 200
    r2 = client.get("/policy/best/u1/squat?k=3")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)
