import time
from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from backend.main import app, hardware_gateway, rover_state


def test_complete_backend_flow():
    with TestClient(app) as client:
        # 1. Backend health
        response = client.get("/api/health")
        assert response.status_code == 200
        health = response.json()
        assert health["status"] == "ok"
        assert health["backend"] is True
        assert health["hardware_connected"] is True

        # 2. Rover is connected
        response = client.get("/api/rover/status")
        assert response.status_code == 200
        status = response.json()
        assert status["connected"] is True

        # 3. Get live telemetry
        response = client.get("/api/rover/telemetry")
        assert response.status_code == 200
        telemetry = response.json()
        assert telemetry["timestamp_ms"] > 0
        assert telemetry["seq"] >= 0
        assert telemetry["us_fl_mm"] > 0.0
        assert telemetry["us_fr_mm"] > 0.0
        assert telemetry["us_l_mm"] > 0.0
        assert telemetry["us_r_mm"] > 0.0
        assert telemetry["tof_front_mm"] > 0.0

        # 4. Switch to autonomous mode
        response = client.post(
            "/api/rover/mode",
            json={"mode": "AUTONOMOUS"},
        )
        assert response.status_code == 200
        assert response.json()["mode"] == "AUTONOMOUS"

        # 5. Verify mode in status
        response = client.get("/api/rover/status")
        assert response.status_code == 200
        status = response.json()
        assert status["mode"] == "AUTONOMOUS"

        # 6. Send velocity command
        response = client.post(
            "/api/rover/command",
            json={
                "command_id": "integration-test-001",
                "timestamp_ms": int(time.time() * 1000),
                "linear_mps": 0.2,
                "angular_rads": 0.0,
                "source": "AUTONOMY",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # 7. Normal stop
        response = client.post("/api/rover/stop")
        assert response.status_code == 200
        assert response.json()["stopped"] is True

        # 8. Emergency stop
        response = client.post("/api/rover/emergency-stop")
        assert response.status_code == 200
        assert response.json()["emergency_stop"] is True

        # 9. Verify emergency state
        response = client.get("/api/rover/status")
        assert response.status_code == 200
        status = response.json()
        assert status["state"] == "EMERGENCY_STOP"

        # 10. Verify movement is blocked during E-stop
        response = client.post(
            "/api/rover/command",
            json={
                "command_id": "integration-test-blocked",
                "timestamp_ms": int(time.time() * 1000),
                "linear_mps": 0.2,
                "angular_rads": 0.0,
                "source": "MANUAL",
            },
        )
        assert response.status_code == 409

        # 11. Reset emergency stop
        response = client.post("/api/rover/emergency-stop/reset")
        assert response.status_code == 200
        assert response.json()["emergency_stop"] is False

        # 12. Verify it does NOT automatically resume motion
        response = client.get("/api/rover/status")
        assert response.status_code == 200
        status = response.json()
        assert status["state"] == "IDLE"
        assert status["mode"] == "MANUAL"

        # 13. Test WebSocket connection and event reception
        with client.websocket_connect("/ws") as ws:
            event = ws.receive_json()
            assert "type" in event
            assert "timestamp_ms" in event
            assert "data" in event
            assert event["type"] in [
                "rover_status",
                "sensor_telemetry",
                "map_update",
                "navigation_update",
                "exploration_update",
                "battery_update",
                "log_event",
                "safety_event",
            ]
