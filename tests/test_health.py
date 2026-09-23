"""Test suite for FastAPI backend startup, health check, CORS, and storage preparation."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """Create a TestClient with lifespan events executed."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify root endpoint responds with metadata and docs links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tiv AI Data Collection Platform API"
    assert data["documentation"] == "/docs"
    assert data["health"] == "/api/v1/health"


def test_health_endpoint(client):
    """Verify /api/v1/health returns 200 OK with connected database and writable storage."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert data["database"]["status"] == "connected"
    assert data["storage"]["writable"] is True
    assert "raw/audio" in data["storage"]["namespaces"]
    assert data["audio_constraints"]["max_size_bytes"] == 26214400
    assert data["audio_constraints"]["min_duration_seconds"] == 0.5
    assert data["consent_version"] == "v1.0-2026-09"


def test_cors_headers(client):
    """Verify CORS headers permit Developer 2's frontend origin."""
    response = client.get(
        "/api/v1/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_docs_endpoint(client):
    """Verify Swagger OpenAPI documentation loads successfully."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_storage_namespaces_exist():
    """Verify local storage directories are created and ready for Milestone 2."""
    base = Path(settings.LOCAL_STORAGE_PATH)
    assert (base / "raw/audio").exists()
    assert (base / "processed/audio").exists()
    assert (base / "quarantine").exists()
    assert (base / "exports/datasets").exists()
