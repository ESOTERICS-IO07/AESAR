import pytest
from backend.models.schemas import (
    CommandRequest,
    CommandSource,
    ModeRequest,
    RoverMode,
    RoverState,
    RoverStatus,
    SensorStatus,
    Telemetry,
    VelocityCommand,
)


def test_rover_state_and_mode_enums():
    assert RoverState.DISCONNECTED == "DISCONNECTED"
    assert RoverState.EMERGENCY_STOP == "EMERGENCY_STOP"
    assert RoverMode.MANUAL == "MANUAL"
    assert RoverMode.AUTONOMOUS == "AUTONOMOUS"
    assert CommandSource.MANUAL == "MANUAL"
    assert CommandSource.AUTONOMY == "AUTONOMY"
    assert CommandSource.SYSTEM == "SYSTEM"


def test_telemetry_schema():
    telem = Telemetry(
        timestamp_ms=1000,
        seq=1,
        us_fl_mm=1200.0,
        us_fr_mm=950.0,
        us_l_mm=760.0,
        us_r_mm=1430.0,
        tof_front_mm=880.0,
    )
    assert telem.us_fl_mm == 1200.0
    assert telem.sensor_status.us_fl == SensorStatus.OK


def test_velocity_command_validation():
    cmd = VelocityCommand(
        command_id="cmd-1",
        timestamp_ms=1000,
        linear_mps=0.5,
        angular_rads=0.1,
        source=CommandSource.MANUAL,
    )
    assert cmd.command_id == "cmd-1"

    # Extra fields forbidden
    with pytest.raises(Exception):
        VelocityCommand(
            command_id="cmd-1",
            timestamp_ms=1000,
            linear_mps=0.5,
            angular_rads=0.1,
            source=CommandSource.MANUAL,
            extra_field="invalid",
        )
