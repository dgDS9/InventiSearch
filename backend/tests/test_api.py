from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "RAG-System/LLM Backend",
    }


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "app": "RAG/LLM Backend",
        "status": "running",
    }