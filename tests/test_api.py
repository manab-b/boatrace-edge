from fastapi.testclient import TestClient

from boatrace_edge.api import app


client = TestClient(app)


def test_index_and_health() -> None:
    index = client.get("/")
    assert index.status_code == 200
    assert "BOAT RACE EDGE" in index.text

    response = client.get("/health")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
