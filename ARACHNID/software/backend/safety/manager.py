from __future__ import annotations

import math
from typing import Any, Dict

from backend.models.schemas import VelocityCommand
from backend.services.rover_state import RoverStateManager


class SafetyManager:
    """
    Software-side safety layer for ARACHNID Rover.

    IMPORTANT:
    This is not the physical safety mechanism.
    Hardware/firmware watchdogs remain responsible for
    physical motor safety.
    """

    def __init__(self, rover_state: RoverStateManager) -> None:
        self.rover_state = rover_state

    def can_accept_command(self) -> bool:
        return not self.rover_state.is_emergency_stopped()

    def validate_velocity_command(self, command: VelocityCommand) -> None:
        if self.rover_state.is_emergency_stopped():
            raise RuntimeError("Rover is in EMERGENCY_STOP state")

        if not math.isfinite(command.linear_mps):
            raise ValueError("linear_mps must be finite")

        if not math.isfinite(command.angular_rads):
            raise ValueError("angular_rads must be finite")

        if command.timestamp_ms <= 0:
            raise ValueError("timestamp_ms must be positive")

        if not command.command_id.strip():
            raise ValueError("command_id cannot be empty")

    def validate_mode_change(self) -> None:
        if self.rover_state.is_emergency_stopped():
            raise RuntimeError("Cannot change mode while emergency stop is active")

    def stop(self) -> Dict[str, Any]:
        self.rover_state.stop()
        return {"success": True, "stopped": True}

    def emergency_stop(self) -> Dict[str, Any]:
        self.rover_state.emergency_stop()
        return {"success": True, "emergency_stop": True}

    def reset_emergency_stop(self) -> Dict[str, Any]:
        self.rover_state.reset_emergency_stop()
        return {"success": True, "emergency_stop": False}
