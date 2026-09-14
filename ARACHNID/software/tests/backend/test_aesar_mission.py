from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app, mission_manager
from backend.models.schemas import MissionState


def test_api_environment_endpoints():
    with TestClient(app) as client:
        res = client.get("/api/environment/current")
        assert res.status_code == 200
        data = res.json()
        assert "available" in data

        res_cal = client.get("/api/environment/calibration")
        assert res_cal.status_code == 200
        cal = res_cal.json()
        assert "dht22" in cal
        assert "soil_moisture" in cal


def test_api_camera_endpoints():
    with TestClient(app) as client:
        res_status = client.get("/api/camera/status")
        assert res_status.status_code == 200
        data = res_status.json()
        assert "state" in data

        res_snap = client.get("/api/camera/snapshot")
        assert res_snap.status_code == 200
        assert res_snap.headers["content-type"] == "image/jpeg"
        assert len(res_snap.content) > 50


def test_api_vision_analyze():
    with TestClient(app) as client:
        res = client.post("/api/vision/analyze", json={})
        assert res.status_code == 200
        data = res.json()
        assert "pests" in data
        assert "defenders" in data
        assert "plant_health" in data


def test_api_aesa_evaluate():
    with TestClient(app) as client:
        payload = {
            "station_id": 1,
            "vision": {
                "pests": [{"name": "aphid", "count": 1, "confidence": 0.9}],
                "defenders": [{"name": "ladybird", "count": 3, "confidence": 0.9}],
            },
            "environment": {
                "temperature_c": 25.0,
                "humidity_percent": 60.0,
                "soil_moisture_percent": 50.0,
                "available": True,
            },
        }
        res = client.post("/api/aesa/evaluate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["ecosystem_state"] == "balanced"
        assert "recommendation" in data


def test_api_mode_toggle():
    with TestClient(app) as client:
        res = client.get("/api/mode")
        assert res.status_code == 200
        initial_mode = res.json()["mode"]

        res_post = client.post("/api/mode", json={"mode": "LIVE"})
        assert res_post.status_code == 200
        assert res_post.json()["mode"] == "LIVE"

        # Revert back to DEMO
        res_back = client.post("/api/mode", json={"mode": "DEMO"})
        assert res_back.status_code == 200
        assert res_back.json()["mode"] == "DEMO"


def test_api_mission_status_and_adhoc():
    with TestClient(app) as client:
        res = client.get("/api/mission/status")
        assert res.status_code == 200
        data = res.json()
        assert "state" in data

        # Test ad-hoc station analysis
        res_adhoc = client.post("/api/mission/analyze-current")
        assert res_adhoc.status_code == 200
        adhoc_data = res_adhoc.json()
        assert "station" in adhoc_data
        assert "analysis" in adhoc_data
        assert adhoc_data["analysis"]["ecosystem_state"] in ("balanced", "moderate", "imbalanced", "unknown")
