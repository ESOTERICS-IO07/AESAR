import pytest
from backend.main import app, rover_state, safety_manager
from fastapi.testclient import TestClient


def test_security_emergency_stop_command_lockout():
    with TestClient(app) as client:
        # 1. Trigger E-stop
        res_estop = client.post("/api/rover/emergency-stop")
        assert res_estop.status_code == 200
        assert rover_state.get_status().state == "EMERGENCY_STOP"

        # 2. Attempt movement command while in E-stop
        res_cmd = client.post(
            "/api/rover/command",
            json={
                "command_id": "malicious-cmd",
                "timestamp_ms": 1000,
                "linear_mps": 0.5,
                "angular_rads": 0.0,
                "source": "MANUAL",
            },
        )
        assert res_cmd.status_code == 409  # Conflict / Locked out
        assert "EMERGENCY_STOP" in res_cmd.json()["detail"]

        # 3. Clean reset
        client.post("/api/rover/emergency-stop/reset")
        assert rover_state.get_status().state == "IDLE"


def test_security_invalid_velocity_rejection():
    with TestClient(app) as client:
        # Attempt string in velocity field
        res_invalid = client.post(
            "/api/rover/command",
            json={
                "command_id": "bad-type-cmd",
                "timestamp_ms": 1000,
                "linear_mps": "invalid_string",
                "angular_rads": 0.0,
                "source": "MANUAL",
            },
        )
        assert res_invalid.status_code == 422  # Unprocessable entity


def test_security_cors_headers_present():
    with TestClient(app) as client:
        res = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert res.status_code == 200
        assert "access-control-allow-origin" in res.headers
