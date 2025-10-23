from fastapi.testclient import TestClient
from neuromotorica_universal.api.app import app

client = TestClient(app)

def test_full_session_flow():
    r = client.post("/v1/session/start", json={"exercise_id":"squat","dt":0.01})
    assert r.status_code == 200
    sid = r.json()["session_id"]

    for _ in range(50):
        rr = client.post(f"/v1/session/{sid}/signal", json={"u":1.0})
        assert rr.status_code == 200
        assert 0.0 <= rr.json()["y"] <= 1.0

    rbest = client.get("/v1/policy/best", params={"session_id":sid, "k":3})
    assert rbest.status_code == 200
    assert len(rbest.json()["cues"]) == 3

    rc = client.post("/v1/policy/outcome", json={"cue_text": rbest.json()['cues'][0], "success": 0.9})
    assert rc.status_code == 200

    rs = client.post(f"/v1/session/{sid}/summary", json={})
    assert rs.status_code == 200
    m = rs.json()["metrics"]
    assert m["peak_force"] > 0.5


def test_session_signal_unknown_session_returns_404():
    sid = "sess-does-not-exist"
    response = client.post(f"/v1/session/{sid}/signal", json={"u": 0.5})

    assert response.status_code == 404
    assert response.json()["detail"] == "session not found"


def test_session_summary_unknown_session_returns_404():
    sid = "sess-missing"
    response = client.post(f"/v1/session/{sid}/summary", json={})

    assert response.status_code == 404
    assert response.json()["detail"] == "session not found"


def test_policy_endpoint_unknown_session_returns_404():
    sid = "sess-unknown"
    response = client.get("/v1/policy/best", params={"session_id": sid, "k": 1})

    assert response.status_code == 404
    assert response.json()["detail"] == "session not found"
