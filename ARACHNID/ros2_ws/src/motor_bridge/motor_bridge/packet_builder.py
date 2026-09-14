"""ARACHNID Motor Bridge Packet Builder.

Translates VelocityCommand dictionaries into differential drive wheel setpoints
and formats JSON packets for the Drive ESP32 adhering to Contract v1.0.0.
"""

from typing import Any, Dict, Optional, Tuple
import time


class PacketBuilder:
    """Builds formatted motor command packets from ROS2 velocity inputs."""

    def __init__(self, wheel_base_m: float = 0.28, wheel_radius_m: float = 0.05):
        self.wheel_base = float(wheel_base_m)
        self.wheel_radius = float(wheel_radius_m)

    def calculate_wheel_speeds(self, linear_mps: float, angular_rads: float) -> Tuple[float, float]:
        """Convert unicycle (linear_mps, angular_rads) to differential wheel velocities (v_left, v_right)."""
        v_left = linear_mps - (angular_rads * self.wheel_base / 2.0)
        v_right = linear_mps + (angular_rads * self.wheel_base / 2.0)
        return round(v_left, 3), round(v_right, 3)

    def build_drive_packet(
        self,
        command_id: str,
        linear_mps: float,
        angular_rads: float,
        source: str = "AUTONOMY",
        e_stop: bool = False,
        timestamp_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Build contract-compliant Drive ESP32 JSON packet.

        Example Packet:
        {"command_id":"AUTO-CMD","linear_mps":0.25,"angular_rads":0.30,"source":"AUTONOMY","timestamp_ms":123456789}
        """
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)

        v_left, v_right = self.calculate_wheel_speeds(linear_mps, angular_rads)

        return {
            "command_id": str(command_id),
            "timestamp_ms": int(timestamp_ms),
            "linear_mps": round(float(linear_mps), 3),
            "angular_rads": round(float(angular_rads), 3),
            "left_mps": v_left,
            "right_mps": v_right,
            "source": str(source),
            "e_stop": bool(e_stop),
        }

    def build_stop_packet(
        self,
        command_id: str = "STOP-CMD",
        source: str = "EMERGENCY_STOP",
        e_stop: bool = True,
    ) -> Dict[str, Any]:
        """Build emergency/zero-velocity stop packet."""
        return self.build_drive_packet(
            command_id=command_id,
            linear_mps=0.0,
            angular_rads=0.0,
            source=source,
            e_stop=e_stop,
        )

    def build_string_packet(self, linear_mps: float, angular_rads: float) -> str:
        """Map ROS2 velocities to exact physical ESP32 #1 string commands."""
        if abs(linear_mps) < 0.05 and abs(angular_rads) < 0.05:
            return "STOP\n"
        
        # Priority to turning if angular rate is dominant
        if abs(angular_rads) > abs(linear_mps):
            if angular_rads > 0:
                return "LEFT\n"
            else:
                return "RIGHT\n"
        else:
            if linear_mps > 0:
                return "FORWARD\n"
            else:
                return "BACKWARD\n"
