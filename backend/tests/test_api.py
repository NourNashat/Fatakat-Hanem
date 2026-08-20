import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.rag_engine import rag_engine

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["chunk_count"] == 303
    assert data["collection"] == "parkville_skin_hair_expert"


def test_catalog_endpoint():
    response = client.get("/api/catalog")
    assert response.status_code == 200
    data = response.json()
    assert data["total_chunks"] == 303
    assert len(data["products"]) > 10
    assert "Shaan" in data["brands"] or "SHAAN" in [b.upper() for b in data["brands"]]
    assert "Clary" in data["brands"] or "CLARY" in [b.upper() for b in data["brands"]]
    assert len(data["sample_questions"]) > 0


def test_manifest_endpoint():
    response = client.get("/api/manifest")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data or "chunk_count" in data


def test_ask_in_scope_answered():
    req_body = {
        "question": "What are the ingredients in Shaan Cleanser?",
        "debug": True
    }
    response = client.post("/api/ask", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["answered", "insufficient_evidence"]
    assert len(data["evidence"]) > 0
    assert any("Shaan" in e["product"] or "Cleanser" in e["product"] for e in data["evidence"])
    assert data["confidence"] in ["high", "medium"]
    assert len(data["suggested_next_action"]) > 0


def test_ask_pregnancy_safety():
    req_body = {
        "question": "How should Clary Booster Shot be used?",
        "debug": True
    }
    response = client.post("/api/ask", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert len(data["evidence"]) > 0
    assert any("Booster Shot" in e["product"] or "Clary" in e["brand"] for e in data["evidence"])


def test_ask_out_of_scope():
    req_body = {
        "question": "What blood tests should be ordered during pregnancy?",
        "debug": True
    }
    response = client.post("/api/ask", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "out_of_scope"
    assert data["confidence"] == "insufficient"


def test_ask_empty_question():
    req_body = {
        "question": "   ",
        "debug": False
    }
    response = client.post("/api/ask", json=req_body)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "insufficient_evidence"
