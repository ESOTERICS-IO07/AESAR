from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import time
from typing import Any, Dict, Optional

from backend.models.schemas import (
    ExplorationData,
    MapData,
    NavigationData,
    Point2D,
    RoverState,
    Telemetry,
)
from backend.hardware.adapters import (
    ExplorationAdapter,
    MapAdapter,
    NavigationAdapter,
    SensorAdapter,
)
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager

logger = logging.getLogger("arachnid.hardware.gateway")

# Contract Constants for Occupancy Grid (200x200 @ 0.05m, origin -5.0, -5.0)
GRID_WIDTH = 200
GRID_HEIGHT = 200
GRID_RESOLUTION_M = 0.05
GRID_ORIGIN_X = -5.0
GRID_ORIGIN_Y = -5.0
SAFETY_STOP_DISTANCE_MM = 180.0  # 0.18m contract safety stop


def _bresenham(x0: int, y0: int, x1: int, y1: int):
    """Bresenham's line algorithm for grid raycasting."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return points


class HardwareGateway:
    """
    Hardware Gateway Provider connecting directly to the Brain ESP32 via TCP / Wi-Fi.

    Architecture:
      React -> FastAPI -> ESP32Provider -> Wi-Fi TCP (192.168.4.1:80) -> Brain ESP32
      Brain ESP32 -> UART -> Rover ESP32 -> BTS7960 -> Motors

    Handles:
      - 5 ultrasonic sensor channels (us_front, us_right, us_left, us_45_right, us_45_left)
      - VL53L0X ToF mounted on scanning servo (angle_deg + distance_mm)
      - Invalid/999 reading normalization to -1 (never treated as clear space)
      - Real-time 2D occupancy grid construction from scanning ToF
      - Rover 1-second command watchdog failsafe
      - Independent physical sensor safety stop before obstacles
      - Discrete Mode A commands: FORWARD, BACKWARD, LEFT, RIGHT, STOP
      - Strict STOP vs EMERGENCY_STOP distinction
    """

    def __init__(
        self,
        rover_state: RoverStateManager,
        websocket_manager: WebSocketManager,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> None:
        self.rover_state = rover_state
        self.websocket_manager = websocket_manager

        # Configuration priority: explicit arg -> env var -> default "192.168.4.1:80"
        self.host = host or os.environ.get("ARACHNID_ESP32_IP", "192.168.4.1")
        self.port = port or int(os.environ.get("ARACHNID_ESP32_PORT", "80"))

        self._running = False
        self._connected = False
        self._seq = 0
        self._main_task: Optional[asyncio.Task] = None
        self._watchdog_task: Optional[asyncio.Task] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        self._last_cmd_time: float = 0.0
        self._last_cmd_is_active: bool = False
        self._last_cmd_str: str = "STOP"
        self._last_cmd_lin: float = 0.0
        self._last_cmd_ang: float = 0.0
        self._reconnect_delay = 1.0

        # Initial cached states
        self._current_telemetry = SensorAdapter.convert_raw_telemetry(
            {
                "us_front_mm": -1.0,
                "us_45_left_mm": -1.0,
                "us_45_right_mm": -1.0,
                "us_left_mm": -1.0,
                "us_right_mm": -1.0,
                "tof_front_mm": -1.0,
            },
            0,
        )

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        logger.info(f"Initializing HardwareGateway connecting to Brain ESP32 at {self.host}:{self.port}")
        self._main_task = asyncio.create_task(self._connection_loop())
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())

    async def stop(self) -> None:
        self._running = False
        if self._watchdog_task is not None:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
            self._watchdog_task = None

        if self._main_task is not None:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass
            self._main_task = None

        if self._writer:
            try:
                res = self._writer.close()
                if asyncio.iscoroutine(res):
                    await res
                if hasattr(self._writer, "wait_closed"):
                    await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None

        self._connected = False
        self.rover_state.set_connected(False)
        logger.info("HardwareGateway stopped cleanly")

    def is_connected(self) -> bool:
        return self._connected

    def get_telemetry(self) -> Telemetry:
        telemetry = self.rover_state.get_telemetry()
        if telemetry is not None:
            return telemetry
        return self._current_telemetry

    def get_current_velocity(self) -> tuple[float, float]:
        if not self._last_cmd_is_active:
            return 0.0, 0.0
        return self._last_cmd_lin, self._last_cmd_ang

    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        command_id = str(command.get("command_id", f"cmd-{int(time.time()*1000)}"))
        lin = float(command.get("linear_mps", 0.0))
        ang = float(command.get("angular_rads", 0.0))

        # Independent physical sensor safety check before moving forward
        if lin > 0.05 and self._is_front_obstacle_too_close():
            logger.warning("Forward command blocked by close physical obstacle (< 180mm)!")
            await self.stop_rover()
            return {
                "success": False,
                "command_id": command_id,
                "error": "OBSTACLE_CRITICAL",
            }

        await self.send_velocity_command(lin, ang)
        return {"success": True, "command_id": command_id}

    async def send_velocity_command(self, linear_mps: float, angular_rads: float) -> None:
        if self.rover_state.is_emergency_stopped():
            logger.warning("Rejecting velocity command: Rover is in EMERGENCY_STOP state")
            return

        # Discrete Mode A command mapping
        if linear_mps > 0.05:
            cmd_str = "FORWARD"
            left_mps, right_mps = 0.20, 0.20
            self._last_cmd_is_active = True
            self._last_cmd_lin = linear_mps
            self._last_cmd_ang = 0.0
        elif linear_mps < -0.05:
            cmd_str = "BACKWARD"
            left_mps, right_mps = -0.20, -0.20
            self._last_cmd_is_active = True
            self._last_cmd_lin = linear_mps
            self._last_cmd_ang = 0.0
        elif angular_rads > 0.05:
            cmd_str = "LEFT"
            left_mps, right_mps = -0.20, 0.20
            self._last_cmd_is_active = True
            self._last_cmd_lin = 0.0
            self._last_cmd_ang = angular_rads
        elif angular_rads < -0.05:
            cmd_str = "RIGHT"
            left_mps, right_mps = 0.20, -0.20
            self._last_cmd_is_active = True
            self._last_cmd_lin = 0.0
            self._last_cmd_ang = angular_rads
        else:
            cmd_str = "STOP"
            left_mps, right_mps = 0.0, 0.0
            self._last_cmd_is_active = False
            self._last_cmd_lin = 0.0
            self._last_cmd_ang = 0.0

        self._last_cmd_time = time.time()
        self._last_cmd_str = cmd_str

        await self._write_raw(cmd_str + "\n")

    async def stop_rover(self) -> None:
        logger.info("Executing normal STOP on Brain/Rover ESP32")
        self._last_cmd_is_active = False
        self._last_cmd_str = "STOP"
        await self._write_raw("STOP\n")
        self.rover_state.stop()

    async def emergency_stop(self) -> None:
        logger.critical("EMERGENCY STOP dispatched to Brain/Rover ESP32 hardware")
        self._last_cmd_is_active = False
        self._last_cmd_str = "STOP"
        await self._write_raw("STOP\n")
        self.rover_state.emergency_stop()

    async def reset_emergency_stop(self) -> None:
        logger.info("Resetting EMERGENCY STOP on Brain/Rover ESP32 hardware")
        await self._write_raw("STOP\n")
        self.rover_state.reset_emergency_stop()

    def _is_front_obstacle_too_close(self) -> bool:
        """Physical sensor check: returns True if an obstacle is within 180mm ahead."""
        t = self._current_telemetry
        front_dists = [t.us_fc_mm, t.us_front_mm, t.tof_front_mm]
        for d in front_dists:
            if d is not None and 0 < d <= SAFETY_STOP_DISTANCE_MM:
                return True
        return False

    async def _write_raw(self, data_str: str) -> None:
        if self._writer:
            try:
                is_closing = False
                if hasattr(self._writer, "is_closing") and callable(self._writer.is_closing):
                    res = self._writer.is_closing()
                    if asyncio.iscoroutine(res):
                        res = await res
                    is_closing = bool(res)

                if not is_closing:
                    res = self._writer.write(data_str.encode("utf-8"))
                    if asyncio.iscoroutine(res):
                        await res
                    if hasattr(self._writer, "drain"):
                        await self._writer.drain()
            except Exception as e:
                logger.error(f"Error writing to Brain ESP32: {e}")

    async def _watchdog_loop(self) -> None:
        """
        Enforces a 2000ms software safety timeout: auto-stops rover if API control becomes stale.
        Continuously refreshes the active command every ~300ms to keep the 1000ms physical hardware watchdog alive.
        """
        while self._running:
            await asyncio.sleep(0.3)
            
            if self.rover_state.is_emergency_stopped():
                self._last_cmd_is_active = False
                continue
                
            if self._last_cmd_is_active:
                if time.time() - self._last_cmd_time > 2.0:
                    logger.warning("Software safety timeout (2000ms) reached without renewal. Auto-stopping rover.")
                    await self.stop_rover()
                else:
                    if self._last_cmd_str == "FORWARD" and self._is_front_obstacle_too_close():
                        logger.warning("Continuous forward refresh blocked by physical obstacle (< 180mm)!")
                        await self.stop_rover()
                    else:
                        await self._write_raw(self._last_cmd_str + "\n")

    async def _connection_loop(self) -> None:
        """Persistent TCP connection loop with exponential backoff."""
        while self._running:
            try:
                logger.info(f"Connecting to Brain ESP32 at {self.host}:{self.port}...")
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=3.0,
                )
                self._writer = writer
                self._connected = True
                self.rover_state.set_connected(True)
                logger.info("Connected to Brain ESP32 successfully!")

                now_ms = int(time.time() * 1000)
                await self.websocket_manager.broadcast(
                    "rover_status",
                    now_ms,
                    self.rover_state.get_status().model_dump(),
                )

                while self._running:
                    line_bytes = await reader.readline()
                    if not line_bytes:
                        logger.warning("Brain ESP32 TCP connection closed by peer.")
                        break

                    line = line_bytes.decode("utf-8", errors="ignore").strip()
                    if line:
                        await self._process_raw_line(line)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Connection attempt to {self.host}:{self.port} failed: {e}")
            finally:
                self._connected = False
                self.rover_state.set_connected(False)
                if self._writer:
                    try:
                        res = self._writer.close()
                        if asyncio.iscoroutine(res):
                            await res
                        if hasattr(self._writer, "wait_closed"):
                            await self._writer.wait_closed()
                    except Exception:
                        pass
                    self._writer = None

            if self._running:
                await asyncio.sleep(self._reconnect_delay)

    async def _process_raw_line(self, line: str) -> None:
        """Parse raw lines from Brain ESP32 (JSON)."""
        now_ms = int(time.time() * 1000)

        # 2. Parse JSON telemetry
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            return

        # Case A: Explicit ToF Scan record
        if raw.get("type") == "tof_scan" or ("angle_deg" in raw and "distance_mm" in raw):
            angle = float(raw.get("angle_deg", 90.0))
            dist = float(raw.get("distance_mm", -1.0))
            await self._handle_tof_scan(angle, dist, now_ms)
            return

        # Case B: Range Telemetry packet
        if "us_fc_mm" in raw or "us_front_mm" in raw or "us_fl_mm" in raw or "ultrasonic" in raw:
            self._seq += 1
            telemetry = SensorAdapter.convert_raw_telemetry(raw, self._seq)
            self._current_telemetry = telemetry
            self.rover_state.set_telemetry(telemetry)

            # Check close obstacle safety stop
            if self._last_cmd_is_active and self._is_front_obstacle_too_close():
                logger.warning("Physical sensor detected close obstacle during forward motion! Immediate STOP.")
                await self.stop_rover()

            # If packet also has scanning ToF fields, update map
            if telemetry.tof_scan and telemetry.tof_scan.angle_deg is not None:
                await self._handle_tof_scan(
                    telemetry.tof_scan.angle_deg,
                    telemetry.tof_scan.distance_mm,
                    now_ms,
                )

            await self.websocket_manager.broadcast("sensor_telemetry", now_ms, telemetry.model_dump())
            await self.websocket_manager.broadcast("rover_status", now_ms, self.rover_state.get_status().model_dump())

    async def _handle_tof_scan(self, angle_deg: float, distance_mm: float, timestamp_ms: int) -> None:
        """Processes a single rotating ToF measurement and updates 2D occupancy grid."""
        # Validity checks: 999 or <= 0 or > 2000 mm is invalid (-1)
        valid = (10.0 <= distance_mm <= 2000.0) and (abs(distance_mm - 999.0) > 1.0)
        norm_dist_mm = distance_mm if valid else -1.0

        scan_payload = {
            "angle_deg": angle_deg,
            "distance_mm": norm_dist_mm,
            "valid": valid,
        }
        await self.websocket_manager.broadcast("tof_scan", timestamp_ms, scan_payload)

        # Forward ToF scan raw data to the backend autonomy engine via websocket for visualization
        if valid:
            pass
