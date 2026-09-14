import time
import pytest
from backend.logging.logger import RoverLogger
from backend.main import app
from fastapi.testclient import TestClient


def test_performance_bounded_logger_memory():
    logger = RoverLogger(max_entries=100)
    for i in range(500):
        logger.info(f"Performance log test #{i}")

    logs = logger.get_logs()
    assert len(logs) == 100
    assert "Performance log test #499" in logs[-1].message


def test_performance_rapid_command_throughput():
    with TestClient(app) as client:
        start = time.time()

        for i in range(10):
            res = client.post(
                "/api/rover/command",
                json={
                    "command_id": f"perf-cmd-{i}",
                    "timestamp_ms": int(time.time() * 1000),
                    "linear_mps": 0.1,
                    "angular_rads": 0.0,
                    "source": "MANUAL",
                },
            )
            assert res.status_code == 200

        elapsed = time.time() - start
        assert elapsed < 3.0


def test_performance_websocket_client_lifecycle():
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            msg = ws.receive_json()
            assert "type" in msg
            assert "data" in msg
