import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from backend.models.schemas import RoverMode, RoverState, SensorStatus
from backend.hardware.gateway import HardwareGateway
from backend.hardware.factory import get_hardware_gateway
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager


def test_factory_creates_esp32_provider():
    rover_state = RoverStateManager()
    ws_manager = WebSocketManager()
    provider = get_hardware_gateway(rover_state, ws_manager, provider_type="real")
    assert isinstance(provider, HardwareGateway)
    assert not provider.is_connected()


def test_esp32_provider_lifecycle_and_commands():
    async def _run():
        rover_state = RoverStateManager()
        ws_manager = WebSocketManager()
        provider = HardwareGateway(rover_state=rover_state, websocket_manager=ws_manager)

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.is_closing.return_value = False

        async def mock_readline():
            await asyncio.sleep(10)
            return b""

        mock_reader.readline = mock_readline

        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            await provider.start()
            await asyncio.sleep(0.01)

            assert provider.is_connected()
            assert rover_state.get_status().connected

            # Send velocity command FORWARD
            res = await provider.send_command({"command_id": "test-1", "linear_mps": 0.25, "angular_rads": 0.0})
            assert res["success"]
            mock_writer.write.assert_called()

            # Normal stop
            await provider.stop_rover()
            assert rover_state.get_status().state == RoverState.IDLE

            # Emergency stop
            await provider.emergency_stop()
            assert rover_state.get_status().state == RoverState.EMERGENCY_STOP
            assert provider.rover_state.is_emergency_stopped()

            # Reset emergency stop
            await provider.reset_emergency_stop()
            assert rover_state.get_status().state == RoverState.IDLE

            await provider.stop()
            assert not provider.is_connected()

    asyncio.run(_run())


def test_esp32_provider_telemetry_normalization():
    async def _run():
        rover_state = RoverStateManager()
        ws_manager = WebSocketManager()
        provider = HardwareGateway(rover_state=rover_state, websocket_manager=ws_manager)

        # Feed a raw line with 999 sentinel on us_45_left and us_right
        raw_json = (
            '{"timestamp_ms":1720000000000,"seq":1,"us_front_mm":350.0,"us_45_left_mm":999.0,'
            '"us_45_right_mm":400.0,"us_left_mm":800.0,"us_right_mm":999.0,"tof_front_mm":360.0}'
        )

        await provider._process_raw_line(raw_json)

        telemetry = provider.get_telemetry()
        assert telemetry.us_front_mm == 350.0
        assert telemetry.us_fc_mm == 350.0
        assert telemetry.sensor_status.us_front == SensorStatus.OK

        # 999 sentinel must become -1 internally and NOT OK
        assert telemetry.us_45_left_mm == -1.0
        assert telemetry.us_fl_mm == -1.0
        assert telemetry.sensor_status.us_45_left in (SensorStatus.TIMEOUT, SensorStatus.DISCONNECTED)

        assert telemetry.us_right_mm == -1.0
        assert telemetry.us_r_mm == -1.0
        assert telemetry.sensor_status.us_right in (SensorStatus.TIMEOUT, SensorStatus.DISCONNECTED)

        assert telemetry.tof_front_mm == 360.0

    asyncio.run(_run())


def test_esp32_provider_close_obstacle_safety():
    async def _run():
        rover_state = RoverStateManager()
        ws_manager = WebSocketManager()
        provider = HardwareGateway(rover_state=rover_state, websocket_manager=ws_manager)

        # Set close obstacle ahead (120mm <= 180mm)
        raw_close = '{"us_front_mm":120.0,"us_45_left_mm":-1,"us_45_right_mm":-1,"us_left_mm":-1,"us_right_mm":-1,"tof_front_mm":120.0}'
        await provider._process_raw_line(raw_close)

        # Attempt to move FORWARD
        res = await provider.send_command({"command_id": "test-fwd", "linear_mps": 0.25, "angular_rads": 0.0})
        # Must be rejected / prevented
        assert not res["success"]
        assert res["error"] == "OBSTACLE_CRITICAL"

        # Backward command should still be allowed
        mock_writer = AsyncMock()
        mock_writer.is_closing.return_value = False
        provider._writer = mock_writer
        res_back = await provider.send_command({"command_id": "test-back", "linear_mps": -0.25, "angular_rads": 0.0})
        assert res_back["success"]

    asyncio.run(_run())

def test_esp32_provider_command_refresh():
    async def _run():
        rover_state = RoverStateManager()
        ws_manager = WebSocketManager()
        provider = HardwareGateway(rover_state=rover_state, websocket_manager=ws_manager)
        
        mock_writer = AsyncMock()
        mock_writer.is_closing.return_value = False
        provider._writer = mock_writer
        provider._running = True
        
        # Start the refresh loop in the background
        refresh_task = asyncio.create_task(provider._watchdog_loop())
        
        # Send a movement command
        await provider.send_velocity_command(0.25, 0.0)
        assert provider._last_cmd_str == "FORWARD"
        assert provider._last_cmd_is_active == True
        
        # Clear mock calls so we can check refresh
        mock_writer.write.reset_mock()
        
        # Wait for refresh loop to tick at least twice (0.3s * 2)
        await asyncio.sleep(0.7)
        
        # Verify it was refreshed multiple times
        assert mock_writer.write.call_count >= 2
        
        # Now trigger normal stop
        await provider.stop_rover()
        assert provider._last_cmd_str == "STOP"
        assert provider._last_cmd_is_active == False
        mock_writer.write.reset_mock()
        
        # Wait for refresh loop again
        await asyncio.sleep(0.4)
        # Should NOT write anything when inactive
        assert mock_writer.write.call_count == 0
        
        # Cleanup
        provider._running = False
        await refresh_task
        
    asyncio.run(_run())

