"""API tests with the Gemini call mocked, so no API key or network is needed."""
from fastapi.testclient import TestClient

from ai_core.gemini_generator import GeminiGenerationError
from legalEaseAPI import routes
from legalEaseAPI.main import app

client = TestClient(app)
PAYLOAD = {
    "document_type": "NDA",
    "parties": "A (Disclosing), B (Receiving)",
    "terms": "Keep secrets; 3 year term",
    "dates": "April 15, 2025",
}


class FakeGenerator:
    def generate_document(self, document_type, parties, terms, dates):
        return f"# {document_type}\n\n## 1. Parties\n{parties} effective {dates}"


def test_root_and_health():
    assert "Welcome" in client.get("/").json()["message"]
    assert client.get("/health").json()["status"] == "ok"


def test_generate_success(monkeypatch):
    monkeypatch.setattr(routes, "get_generator", lambda: FakeGenerator())
    r = client.post("/generate", json=PAYLOAD)
    assert r.status_code == 200 and r.json()["document"].startswith("# NDA")


def test_generate_validation_error():
    r = client.post("/generate", json={**PAYLOAD, "document_type": ""})
    assert r.status_code == 422


def test_generate_missing_api_key_returns_503(monkeypatch):
    def boom():
        raise GeminiGenerationError("GEMINI_API_KEY is not set.", 503)
    monkeypatch.setattr(routes, "get_generator", boom)
    r = client.post("/generate", json=PAYLOAD)
    assert r.status_code == 503 and "GEMINI_API_KEY" in r.json()["detail"]
