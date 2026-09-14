import asyncio
import pytest
from backend.models.schemas import RoverState
from backend.hardware.simulator.scenarios import SimulationScenario
from backend.hardware.simulator.simulated_provider import SimulatedHardwareGateway
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager


def test_simulated_provider_lifecycle_and_scenarios():
    async def _run():
        rover_state = RoverStateManager()
        ws_manager = WebSocketManager()
        provider = SimulatedHardwareGateway(rover_state=rover_state, websocket_manager=ws_manager)

        await provider.start()
        assert provider.is_connected()
        assert rover_state.get_status().connected

        # Send command
        ack = await provider.send_command({"command_id": "sim-test-1", "linear_mps": 0.4, "angular_rads": 0.0})
        assert ack["success"]
        assert ack["command_id"] == "sim-test-1"

        # Scenario: Obstacle Ahead
        provider.set_scenario(SimulationScenario.OBSTACLE_AHEAD)
        telemetry = provider.get_telemetry()
        assert telemetry.tof_front_mm < 300.0

        # Scenario: Disconnect & Reconnect
        provider.set_scenario(SimulationScenario.ROS2_DISCONNECT)
        assert not provider.is_connected()
        assert not rover_state.get_status().connected

        provider.set_scenario(SimulationScenario.ROS2_RECONNECT)
        assert provider.is_connected()
        assert rover_state.get_status().connected

        # Emergency stop
        await provider.emergency_stop()
        assert rover_state.get_status().state == RoverState.EMERGENCY_STOP

        # Reset emergency stop
        await provider.reset_emergency_stop()
        assert rover_state.get_status().state == RoverState.IDLE

        await provider.stop()
        assert not provider.is_connected()

    asyncio.run(_run())
