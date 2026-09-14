from __future__ import annotations

import asyncio
from typing import Set

from fastapi import WebSocket


ALLOWED_EVENTS = {
    "rover_status",
    "sensor_telemetry",
    "tof_scan",
    "map_update",
    "navigation_update",
    "exploration_update",
    "battery_update",
    "log_event",
    "safety_event",
    "agri_telemetry",
    "camera_status",
    "mission_status",
    "station_started",
    "station_completed",
    "field_card_generated",
    "aesa_update",
}


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(
        self,
        event_type: str,
        timestamp_ms: int,
        data: dict,
    ) -> None:
        if event_type not in ALLOWED_EVENTS:
            raise ValueError(f"Unsupported WebSocket event: {event_type}")

        message = {
            "type": event_type,
            "timestamp_ms": timestamp_ms,
            "data": data,
        }

        async with self._lock:
            connections = list(self._connections)

        dead_connections = []

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            await self.disconnect(websocket)

    async def count(self) -> int:
        async with self._lock:
            return len(self._connections)