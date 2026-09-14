import asyncio
import pytest
from fastapi.testclient import TestClient

from backend.main import app, websocket_manager


def test_websocket_connect_and_broadcast():
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            # Client connects successfully and receives telemetry broadcast
            data = ws.receive_json()
            assert "type" in data
            assert "timestamp_ms" in data
            assert "data" in data


def test_websocket_manager_unsupported_event():
    manager = websocket_manager

    with pytest.raises(ValueError, match="Unsupported WebSocket event"):
        asyncio.run(manager.broadcast("invalid_event", 100, {}))
