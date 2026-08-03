from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import DocumentChunk

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_returns_citations_from_retrieved_chunks(monkeypatch):
    fake_chunks = [
        DocumentChunk(
            id="chunk-1",
            document_id="doc-1",
            content="Providers of high-risk AI systems shall establish a risk management system.",
            metadata={"regulation": "AI Act", "article": "Article 9"},
        )
    ]
    monkeypatch.setattr("app.api.chat.retrieve", lambda *args, **kwargs: fake_chunks)

    response = client.post(
        "/api/chat",
        json={"user_id": "demo-user", "message": "Does the AI Act apply to us?", "language": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["citations"]) == 1
    assert body["citations"][0]["regulation"] == "AI Act"
    assert body["citations"][0]["article"] == "Article 9"
    assert body["citations"][0]["chunk_id"] == "chunk-1"
