from fastapi.testclient import TestClient
from pipeline.api import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
