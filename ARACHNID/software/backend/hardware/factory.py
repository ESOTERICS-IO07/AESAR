from __future__ import annotations

import os
from typing import Optional

from backend.hardware.base import HardwareGatewayBase
from backend.hardware.simulator.simulated_provider import SimulatedHardwareGateway
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager


def get_hardware_gateway(
    rover_state: RoverStateManager,
    websocket_manager: WebSocketManager,
    provider_type: Optional[str] = None,
) -> HardwareGatewayBase:
    """
    Factory creating either HardwareGateway or SimulatedHardwareGateway.

    Selection priority:
    1. Explicit provider_type argument ('real', 'simulated')
    2. Environment variable ARACHNID_HARDWARE_GATEWAY
    3. Default to SimulatedHardwareGateway for local testing
    """
    selected = (provider_type or os.environ.get("ARACHNID_HARDWARE_GATEWAY", "simulated")).lower()

    if selected == "real":
        from backend.hardware.gateway import HardwareGateway

        return HardwareGateway(
            rover_state=rover_state,
            websocket_manager=websocket_manager,
        )

    return SimulatedHardwareGateway(
        rover_state=rover_state,
        websocket_manager=websocket_manager,
    )

