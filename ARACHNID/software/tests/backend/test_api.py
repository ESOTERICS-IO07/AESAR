from fastapi.testclient import TestClient

# pyrefly: ignore [missing-import]
from backend.main import app, rover_state


def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["backend"] is True
        assert data["hardware_connected"] is True


def test_rover_status():
    with TestClient(app) as client:
        response = client.get("/api/rover/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        assert "state" in data
        assert "mode" in data
        assert "battery_percent" in data


def test_telemetry():
    with TestClient(app) as client:
        response = client.get("/api/rover/telemetry")
        assert response.status_code == 200
        data = response.json()
        assert "us_fl_mm" in data
        assert "us_fr_mm" in data
        assert "us_l_mm" in data
        assert "us_r_mm" in data
        assert "tof_front_mm" in data
        assert "sensor_status" in data


def test_set_autonomous_mode():
    with TestClient(app) as client:
        rover_state.reset_emergency_stop()
        response = client.post(
            "/api/rover/mode",
            json={"mode": "AUTONOMOUS"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mode"] == "AUTONOMOUS"


def test_velocity_command():
    with TestClient(app) as client:
        rover_state.reset_emergency_stop()
        response = client.post(
            "/api/rover/command",
            json={
                "command_id": "test-123",
                "timestamp_ms": 1000,
                "linear_mps": 0.2,
                "angular_rads": 0.0,
                "source": "MANUAL",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["command_id"] == "test-123"


def test_normal_stop():
    with TestClient(app) as client:
        response = client.post("/api/rover/stop")
        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "stopped": True,
        }


def test_emergency_stop_and_block_commands():
    with TestClient(app) as client:
        # Trigger E-stop
        response = client.post("/api/rover/emergency-stop")
        assert response.status_code == 200
        assert response.json() == {
            "success": True,
            "emergency_stop": True,
        }

        # Attempting motion command must be rejected with 409
        cmd_response = client.post(
            "/api/rover/command",
            json={
                "command_id": "blocked-command",
                "timestamp_ms": 1000,
                "linear_mps": 0.2,
                "angular_rads": 0.0,
                "source": "MANUAL",
            },
        )
        assert cmd_response.status_code == 409

        # Attempting mode change must be rejected with 409
        mode_response = client.post(
            "/api/rover/mode",
            json={"mode": "AUTONOMOUS"},
        )
        assert mode_response.status_code == 409

        # Reset E-stop
        reset_response = client.post("/api/rover/emergency-stop/reset")
        assert reset_response.status_code == 200
        assert reset_response.json() == {
            "success": True,
            "emergency_stop": False,
        }


def test_map():
    with TestClient(app) as client:
        response = client.get("/api/map")
        assert response.status_code == 200
        data = response.json()
        assert "resolution_m_per_cell" in data
        assert "width" in data
        assert "height" in data
        assert "origin" in data
        assert "data" in data
        
        # Verify it's using the new GlobalMapper (400x400)
        assert data["width"] == 400
        assert data["height"] == 400
        
        # Verify a live ToF update changes the map
        from backend.main import autonomy_engine
        
        # Inject a ToF measurement into the autonomy engine's mapper manually
        # This simulates the engine picking up a live ToF telemetry reading
        autonomy_engine.mapper.update_from_tof((0.0, 0.0, 0.0), 90.0, 1500.0) # 1.5m straight ahead
        
        # Fetch the map again
        response2 = client.get("/api/map")
        data2 = response2.json()
        
        # 100 is the occupied cell value. Prove the map was modified.
        assert 100 in data2["data"]


def test_navigation():
    with TestClient(app) as client:
        response = client.get("/api/navigation")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "goal" in data
        assert "path" in data


def test_exploration():
    with TestClient(app) as client:
        response = client.get("/api/exploration")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "explored_percent" in data
        assert "frontier_count" in data
        assert "current_goal" in data


def test_logs():
    with TestClient(app) as client:
        response = client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
