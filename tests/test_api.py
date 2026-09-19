from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app, raise_server_exceptions=False)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_missing_incident_returns_structured_error() -> None:
    response = client.get("/incidents/missing")

    assert response.status_code == 404

    body = response.json()

    assert body["error"] == "not_found"
    assert body["message"] == "Incident 'missing' was not found."
    assert body["request_id"]


def test_timeline_endpoint() -> None:
    response = client.get("/incidents/inc-1/timeline")

    assert response.status_code == 200
    assert response.json() == []


def test_diagnosis_endpoint() -> None:
    response = client.get("/incidents/inc-1/diagnosis")

    assert response.status_code == 200

    body = response.json()

    assert body["incident_id"] == "inc-1"
    assert body["diagnosis"] is None


def test_evidence_endpoint() -> None:
    response = client.get("/incidents/inc-1/evidence")

    assert response.status_code == 200
    assert response.json() == []


def test_recommendations_endpoint() -> None:
    response = client.get("/incidents/inc-1/recommendations")

    assert response.status_code == 200
    assert response.json() == []


def test_request_id_is_preserved() -> None:
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_internal_errors_do_not_expose_traceback() -> None:
    from backend.api.app import app

    @app.get("/test-internal-error")
    def internal_error_route():
        raise RuntimeError("secret internal failure")

    response = client.get("/test-internal-error")

    assert response.status_code == 500

    body = response.json()

    assert body["error"] == "internal_error"
    assert body["message"] == "An internal error occurred."
    assert "traceback" not in body
    assert "secret internal failure" not in body
    assert body["request_id"]