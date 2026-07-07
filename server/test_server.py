from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_stadium_pings_endpoint():
    """Verify that stadium snapshots return correct structures and dynamic counts."""
    response = client.get("/api/stadium-pings")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "facilities" in data
    assert "crowd_zones" in data
    assert "summary" in data
    assert "avg_gate_wait" in data["summary"]

def test_benchmark_endpoint():
    """Verify that the RAPIDS execution benchmark calculates results for both CPU & GPU paths."""
    payload = {
        "data_size": 10000,
        "warning_threshold": 70
    }
    response = client.post("/api/benchmark", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "cpu" in data
    assert "gpu" in data
    assert "acceleration" in data
    assert "top_hotspots" in data
    
    # Check scaling outputs
    assert data["cpu"]["execution_time_ms"] > 0
    assert data["gpu"]["execution_time_ms"] > 0
    assert data["acceleration"]["speedup_multiplier"] >= 1.0

def test_cloud_sync_endpoint():
    """Verify GCS and BigQuery streaming mock behaviors."""
    payload = {
        "sync_to_gcs": True,
        "sync_to_bq": True
    }
    response = client.post("/api/gcp/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["gcs"]["status"] == "COMPLETED"
    assert "bytes_saved" in data["gcs"]
    assert "rows_inserted" in data["bigquery"]

def test_gemini_advisory_fan():
    """Verify that Gemini outputs fan concierge suggestions and markdown tables on food query."""
    payload = {
        "prompt": "where can i find tacos?",
        "user_context": "fan",
        "preferred_lang": "en"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "tacos" in data["title"].lower() or "food" in data["title"].lower()
    assert len(data["recommendations"]) > 0
    assert data["table"]["headers"] == ["Concession Vendor", "Category", "Section Location", "Queue wait"]

def test_gemini_advisory_organizer():
    """Verify organizer context returns crowd congestion analysis reports."""
    payload = {
        "prompt": "analyze bottleneck risk zones",
        "user_context": "organizer",
        "preferred_lang": "en"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "crowd" in data["title"].lower() or "congestion" in data["title"].lower()
    assert "CZ-104" in [row[0] for row in data["table"]["rows"]] or "CZ-101" in [row[0] for row in data["table"]["rows"]]

def test_gemini_advisory_multilingual():
    """Verify that requesting spanish outputs translation headers."""
    payload = {
        "prompt": "gates status",
        "user_context": "fan",
        "preferred_lang": "es"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["title"].startswith("[ES]")
    assert all(h.startswith("[ES]") for h in data["table"]["headers"])

def test_security_headers():
    """Verify that HTTP security headers are correctly present in API responses."""
    response = client.get("/api/stadium-pings")
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

def test_cors_headers():
    """Verify CORS configuration allows defined origins and restricts wildcard requests."""
    # Test allowed origin
    headers = {"Origin": "http://localhost:5173"}
    response = client.options("/api/stadium-pings", headers=headers)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Test disallowed origin
    headers = {"Origin": "http://malicious-site.com"}
    response = client.options("/api/stadium-pings", headers=headers)
    assert "access-control-allow-origin" not in response.headers or response.headers.get("access-control-allow-origin") != "http://malicious-site.com"

def test_benchmark_validation_invalid_bounds():
    """Verify that the benchmark API rejects inputs that violate bounds."""
    # Under limit size
    payload = {"data_size": 99, "warning_threshold": 70}
    response = client.post("/api/benchmark", json=payload)
    assert response.status_code == 422
    
    # Over limit threshold
    payload = {"data_size": 1000, "warning_threshold": 105}
    response = client.post("/api/benchmark", json=payload)
    assert response.status_code == 422

def test_gemini_advisory_validation_invalid_bounds():
    """Verify that Gemini advisory rejects invalid lengths or missing parameters."""
    payload = {
        "prompt": "",
        "user_context": "fan",
        "preferred_lang": "en"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 422

def test_gemini_advisory_permutations():
    """Verify French translations, default fan help, staff context, and default organizer instructions."""
    # French
    payload = {
        "prompt": "gates status",
        "user_context": "fan",
        "preferred_lang": "fr"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    assert response.json()["title"].startswith("[FR]")
    
    # Default Fan Help
    payload = {
        "prompt": "general stadium help query",
        "user_context": "fan",
        "preferred_lang": "en"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    assert "multilingual fan assistant" in response.json()["title"].lower()

    # Staff shift context
    payload = {
        "prompt": "where is my volunteer shift?",
        "user_context": "organizer",
        "preferred_lang": "en"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    assert "staff" in response.json()["title"].lower() or "allocation" in response.json()["title"].lower()

    # Default Organizer Help
    payload = {
        "prompt": "random operations query",
        "user_context": "organizer",
        "preferred_lang": "en"
    }
    response = client.post("/api/ai/advise", json=payload)
    assert response.status_code == 200
    assert "desk" in response.json()["title"].lower() or "operations" in response.json()["title"].lower()

def test_cloud_sync_permutations():
    """Verify BigQuery and GCS sync operations with toggled values."""
    payload = {"sync_to_gcs": False, "sync_to_bq": False}
    response = client.post("/api/gcp/sync", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Skipped GCS export" in data["gcs"]["message"]
    assert "Skipped BigQuery stream" in data["bigquery"]["message"]
