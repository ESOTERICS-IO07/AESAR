import pytest

# pyrefly: ignore [missing-import]
from backend.models.schemas import (
    CommandSource,
    VelocityCommand,
)
# pyrefly: ignore [missing-import]
from backend.safety.manager import SafetyManager
# pyrefly: ignore [missing-import]
from backend.services.rover_state import RoverStateManager


def make_command(**overrides):
    data = {
        "command_id": "test-command",
        "timestamp_ms": 1000,
        "linear_mps": 0.2,
        "angular_rads": 0.0,
        "source": CommandSource.MANUAL,
    }

    data.update(overrides)

    return VelocityCommand(**data)


def test_valid_command():
    state = RoverStateManager()
    state.set_connected(True)

    safety = SafetyManager(state)

    safety.validate_velocity_command(
        make_command()
    )


def test_emergency_stop_rejects_command():
    state = RoverStateManager()
    state.set_connected(True)
    state.emergency_stop()

    safety = SafetyManager(state)

    with pytest.raises(RuntimeError):
        safety.validate_velocity_command(
            make_command()
        )


def test_nan_linear_velocity_rejected():
    state = RoverStateManager()
    state.set_connected(True)

    safety = SafetyManager(state)

    with pytest.raises(ValueError):
        safety.validate_velocity_command(
            make_command(linear_mps=float("nan"))
        )


def test_infinite_angular_velocity_rejected():
    state = RoverStateManager()
    state.set_connected(True)

    safety = SafetyManager(state)

    with pytest.raises(ValueError):
        safety.validate_velocity_command(
            make_command(angular_rads=float("inf"))
        )
