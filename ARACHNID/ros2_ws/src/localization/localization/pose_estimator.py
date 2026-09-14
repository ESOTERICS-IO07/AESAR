"""ARACHNID Pose Estimator.

Maintains current robot pose in the map frame and calculates confidence.
"""

from typing import Any, Dict, Optional
import time


class PoseEstimator:
    """Estimates robot pose in world map frame."""

    def __init__(self, frame: str = "map"):
        self.frame = frame
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.confidence = 1.0

    def update(
        self,
        odom_packet: Dict[str, Any],
        fused_yaw: float,
        last_update_age_s: float = 0.0,
    ) -> Dict[str, Any]:
        """Update pose state from fused inputs.

        Args:
            odom_packet: Validated OdometryPacket dictionary.
            fused_yaw: Fused orientation in radians.
            last_update_age_s: Latency/age of latest measurement in seconds.

        Returns:
            PosePacket dictionary adhering to Contract v1.0.0.
        """
        self.x = float(odom_packet.get("x_m", 0.0))
        self.y = float(odom_packet.get("y_m", 0.0))
        self.yaw = float(fused_yaw)

        # Confidence calculation: decreases with sensor age / latency
        base_confidence = 0.99
        latency_penalty = min(0.5, last_update_age_s * 0.2)
        self.confidence = max(0.1, min(1.0, base_confidence - latency_penalty))

        timestamp_ms = odom_packet.get("timestamp_ms", int(time.time() * 1000))

        return {
            "timestamp_ms": int(timestamp_ms),
            "frame": self.frame,
            "x_m": round(self.x, 3),
            "y_m": round(self.y, 3),
            "yaw_rad": round(self.yaw, 3),
            "confidence": round(self.confidence, 2),
        }