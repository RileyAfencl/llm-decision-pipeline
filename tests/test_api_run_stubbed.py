from fastapi.testclient import TestClient
import pipeline.api as api


def test_run_returns_clean_response(monkeypatch):
    # Stub out the orchestrator call so no steps execute and no OpenAI is touched.
    def fake_run_pipeline(steps, initial_data):
        return {
            "question": initial_data["question"],
            "action": "DO_NOTHING",
            "validated": {"ok": True},
            "score": {"total": 1.0},
            "grade": {"label": "A"},
            "repaired": False,
            "reasked": False,
            "best": {"id": "best1"},
            "decision_reason": {"why": "stubbed"},
        }

    monkeypatch.setattr(api, "run_pipeline", fake_run_pipeline)

    client = TestClient(api.app)
    resp = client.post("/run", json={"question": "hi", "break_json": False})

    assert resp.status_code == 200
    data = resp.json()

    # Verify shape + stability
    assert data["question"] == "hi"
    assert data["action"] == "DO_NOTHING"
    assert data["validated"] == {"ok": True}
    assert data["decision_reason"] == {"why": "stubbed"}
