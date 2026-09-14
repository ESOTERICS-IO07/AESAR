from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from backend.models.schemas import ExplorationData, MapData, NavigationData, Telemetry


class HardwareGatewayBase(ABC):
    """
    Abstract Base Class for ARACHNID Hardware Gateways.
    Both SimulatedHardwareGateway and HardwareGateway adhere to this contract interface.
    """

    @abstractmethod
    async def start(self) -> None:
        """Start provider background loops and subscriptions."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Stop provider background loops and cleanly disconnect."""
        raise NotImplementedError

    @abstractmethod
    def get_telemetry(self) -> Telemetry:
        """Retrieve the latest validated sensor telemetry."""
        raise NotImplementedError

    @abstractmethod
    def get_map(self) -> MapData:
        """Retrieve the latest occupancy grid map."""
        raise NotImplementedError

    @abstractmethod
    def get_navigation(self) -> NavigationData:
        """Retrieve the latest navigation trajectory & goal state."""
        raise NotImplementedError

    @abstractmethod
    def get_exploration(self) -> ExplorationData:
        """Retrieve the latest frontier exploration metrics."""
        raise NotImplementedError

    @abstractmethod
    async def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Transmit a velocity command to the robot and return acknowledgement."""
        raise NotImplementedError

    @abstractmethod
    async def send_velocity_command(self, linear_mps: float, angular_rads: float) -> None:
        """Transmit raw velocity command."""
        raise NotImplementedError

    @abstractmethod
    async def stop_rover(self) -> None:
        """Execute normal stop."""
        raise NotImplementedError

    @abstractmethod
    async def emergency_stop(self) -> None:
        """Execute emergency stop and latch hardware safety."""
        raise NotImplementedError

    @abstractmethod
    async def reset_emergency_stop(self) -> None:
        """Reset emergency stop condition."""
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if physical robot connection is active."""
        raise NotImplementedError
