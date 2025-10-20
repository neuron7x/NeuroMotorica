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
    assert "fft_threshold" in data["scenarios"]["config"]
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
    payload = {
        "user_id": "u1",
        "exercise_id": "squat",
        "cue_text": "Тримай темп",
        "success": True,
        "reps": 12,
        "metrics": {"twitch": 0.42, "snr": 18.0},
        "extended": True,
        "profile": "baseline",
    }
    r = client.post("/policy/outcome", json=payload)
    assert r.status_code == 200
    out = r.json()
    assert out["status"] == "ok"
    assert out["outcome"]["reps"] == payload["reps"]
    assert out["outcome"]["metrics"] == payload["metrics"]
    assert out["outcome"]["extended"] is True
    assert out["outcome"]["success"] == 1
    assert out["outcome"]["profile"] == payload["profile"]
    r2 = client.get("/policy/best/u1/squat?k=3&profile=baseline")
    assert r2.status_code == 200
    ranked = r2.json()
    assert ranked["user_id"] == "u1"
    assert ranked["exercise_id"] == "squat"
    assert ranked["profile"] == "baseline"
    assert isinstance(ranked["recommendations"], list)
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert metrics.headers.get("content-type", "").startswith("text/plain")


def test_cli_simulate_extended_outputs_metrics():
    result = runner.invoke(app, [
        "simulate-extended", "--seconds", "0.3", "--units", "16", "--rate", "15",
        "--failure-bias", "0.05"
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    metrics = data["metrics"]
    assert "failure_rate" in metrics
    assert "jitter_ms" in metrics
    assert "cv_force" in metrics


def test_cli_optimize_profile_command():
    result = runner.invoke(app, [
        "optimize", "profile", "--seconds", "0.2", "--units", "12", "--rate", "8", "--repeats", "2"
    ])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert "metrics" in data
    assert "runtime_ms" in data["metrics"]
    assert isinstance(data["recommendations"], list)
