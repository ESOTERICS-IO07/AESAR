import os
import pytest
from backend.hardware.factory import get_hardware_gateway
from backend.hardware.simulator.simulated_provider import SimulatedHardwareGateway
from backend.hardware.gateway import HardwareGateway
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager


def test_factory_default_simulated():
    rover_state = RoverStateManager()
    ws_manager = WebSocketManager()
    provider = get_hardware_gateway(rover_state, ws_manager)
    assert isinstance(provider, SimulatedHardwareGateway)


def test_factory_explicit_real():
    rover_state = RoverStateManager()
    ws_manager = WebSocketManager()
    provider = get_hardware_gateway(rover_state, ws_manager, provider_type="real")
    assert isinstance(provider, HardwareGateway)


def test_factory_env_override(monkeypatch):
    monkeypatch.setenv("ARACHNID_HARDWARE_GATEWAY", "real")
    rover_state = RoverStateManager()
    ws_manager = WebSocketManager()
    provider = get_hardware_gateway(rover_state, ws_manager)
    assert isinstance(provider, HardwareGateway)
