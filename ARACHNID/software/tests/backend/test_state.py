# pyrefly: ignore [missing-import]
from backend.models.schemas import RoverMode, RoverState
# pyrefly: ignore [missing-import]
from backend.services.rover_state import RoverStateManager


def test_initial_state():
    state = RoverStateManager()

    status = state.get_status()

    assert status.connected is False
    assert status.state == RoverState.DISCONNECTED
    assert status.mode == RoverMode.MANUAL
    assert status.battery_percent == -1


def test_connection():
    state = RoverStateManager()

    state.set_connected(True)

    status = state.get_status()

    assert status.connected is True
    assert status.state == RoverState.IDLE


def test_mode_change():
    state = RoverStateManager()

    state.set_connected(True)
    state.set_mode(RoverMode.AUTONOMOUS)

    status = state.get_status()

    assert status.mode == RoverMode.AUTONOMOUS
    assert status.state == RoverState.AUTONOMOUS


def test_emergency_stop():
    state = RoverStateManager()

    state.set_connected(True)
    state.set_mode(RoverMode.AUTONOMOUS)
    state.emergency_stop()

    assert state.is_emergency_stopped()
    assert state.get_status().state == RoverState.EMERGENCY_STOP


def test_emergency_reset_does_not_resume():
    state = RoverStateManager()

    state.set_connected(True)
    state.set_mode(RoverMode.AUTONOMOUS)
    state.emergency_stop()
    state.reset_emergency_stop()

    status = state.get_status()

    assert status.state == RoverState.IDLE
    assert status.mode == RoverMode.MANUAL
