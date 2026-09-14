from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from backend.models.schemas import (
    ExplorationData,
    MapData,
    NavigationData,
    Point2D,
    Telemetry,
)
from backend.hardware.simulator.engine import SimulationEngine
from backend.hardware.simulator.scenarios import SimulationScenario
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager

logger = logging.getLogger("arachnid.hardware.simulator")


class SimulatedHardwareGateway:
    """
    High-Fidelity Integration Simulator for ARACHNID Software Testing.
    Implements the complete hardware gateway interface for testing without hardware.
    """

    def __init__(
        self,
        rover_state: RoverStateManager,
        websocket_manager: WebSocketManager,
    ) -> None:
        self.rover_state = rover_state
        self.websocket_manager = websocket_manager
        self.engine = SimulationEngine()

        self._running = False
        self._connected = True
        self._task: Optional[asyncio.Task] = None
        self._seq = 0
        self._last_cmd_lin = 0.0
        self._last_cmd_ang = 0.0

    def is_connected(self) -> bool:
        if self.engine.scenario == SimulationScenario.ROS2_DISCONNECT:
            return False
        return self._connected

    def set_scenario(self, scenario: SimulationScenario) -> None:
        logger.info(f"Simulator scenario switched to: {scenario.value}")
        self.engine.set_scenario(scenario)
        if scenario == SimulationScenario.ROS2_DISCONNECT:
            self._connected = False
            self.rover_state.set_connected(False)
        elif scenario == SimulationScenario.ROS2_RECONNECT:
            self._connected = True
            self.rover_state.set_connected(True)
            self.engine.set_scenario(SimulationScenario.NORMAL)
        elif scenario == SimulationScenario.EMERGENCY_STOP:
            self.rover_state.emergency_stop()

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._connected = True
        self.rover_state.set_connected(True)
        logger.info("SimulatedHardwareGateway started")
        self._task = asyncio.create_task(self._simulation_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._connected = False
        self.rover_state.set_connected(False)
        logger.info("SimulatedHardwareGateway stopped cleanly")

    def get_current_velocity(self) -> tuple[float, float]:
        return self._last_cmd_lin, self._last_cmd_ang

    def get_telemetry(self) -> Telemetry:
        return self.engine.get_telemetry_model(self._seq)

    def get_map(self) -> MapData:
        return self.engine.get_map_model()

    def get_navigation(self) -> NavigationData:
        return self.engine.get_navigation_model()

    def get_exploration(self) -> ExplorationData:
        return self.engine.get_exploration_model()

    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        command_id = str(command.get("command_id", f"sim-cmd-{int(time.time()*1000)}"))
        lin = float(command.get("linear_mps", 0.0))
        ang = float(command.get("angular_rads", 0.0))

        await self.send_velocity_command(lin, ang)
        return {
            "success": True,
            "command_id": command_id,
        }

    async def send_velocity_command(self, linear_mps: float, angular_rads: float) -> None:
        self._last_cmd_lin = linear_mps
        self._last_cmd_ang = angular_rads
        self.engine.set_velocity_target(linear_mps, angular_rads)
        logger.debug(f"Simulator target velocity updated: linear={linear_mps}, angular={angular_rads}")

    async def stop_rover(self) -> None:
        self._last_cmd_lin = 0.0
        self._last_cmd_ang = 0.0
        self.engine.set_velocity_target(0.0, 0.0)
        self.rover_state.stop()

    async def emergency_stop(self) -> None:
        self.engine.set_scenario(SimulationScenario.EMERGENCY_STOP)
        self._last_cmd_lin = 0.0
        self._last_cmd_ang = 0.0
        self.engine.set_velocity_target(0.0, 0.0)
        self.rover_state.emergency_stop()

    async def reset_emergency_stop(self) -> None:
        if self.engine.scenario == SimulationScenario.EMERGENCY_STOP:
            self.engine.set_scenario(SimulationScenario.NORMAL)
        self.rover_state.reset_emergency_stop()

    async def _simulation_loop(self) -> None:
        last_time = time.time()

        while self._running:
            try:
                now = time.time()
                dt = now - last_time
                last_time = now

                # 1. Update Physics
                self.engine.update_physics(dt)

                # 2. Skip updates if disconnected in scenario
                if self.engine.scenario == SimulationScenario.ROS2_DISCONNECT:
                    await asyncio.sleep(0.2)
                    continue

                # 3. Generate Telemetry
                self._seq += 1
                now_ms = int(time.time() * 1000)
                telemetry = self.engine.get_telemetry_model(self._seq)

                self.rover_state.set_telemetry(telemetry)
                self.rover_state.set_battery(self.engine.battery_percent)

                # 4. Broadcast over WebSocket
                await self.websocket_manager.broadcast(
                    "sensor_telemetry",
                    now_ms,
                    telemetry.model_dump(),
                )

                await self.websocket_manager.broadcast(
                    "rover_status",
                    now_ms,
                    self.rover_state.get_status().model_dump(),
                )

                await self.websocket_manager.broadcast(
                    "battery_update",
                    now_ms,
                    {"battery_percent": round(self.engine.battery_percent, 1)},
                )

                # Periodic Map update
                if self._seq % 5 == 0:
                    map_data = self.engine.get_map_model()
                    await self.websocket_manager.broadcast(
                        "map_update",
                        now_ms,
                        map_data.model_dump(),
                    )

                await asyncio.sleep(0.2)  # 5 Hz update rate

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(0.5)
