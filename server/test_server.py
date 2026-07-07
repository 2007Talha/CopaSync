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
