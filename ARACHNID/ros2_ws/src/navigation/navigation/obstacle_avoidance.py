"""ARACHNID Reactive Obstacle Avoidance.

Monitors short-range proximity sensors to enforce dynamic slowdown
and emergency safety stopping before collisions occur.
"""

from typing import Any, Dict, Tuple


class ObstacleAvoidance:
    """Evaluates short-range proximity sensor readings against safety limits."""

    def __init__(
        self,
        safety_stop_distance_m: float = 0.18,
        slowdown_distance_m: float = 0.40,
    ):
        self.safety_stop_m = float(safety_stop_distance_m)
        self.slowdown_m = float(slowdown_distance_m)

    def evaluate(self, range_data: Dict[str, Any]) -> Tuple[bool, float, str]:
        """Evaluates sensor readings.

        Args:
            range_data: Dictionary containing RangePacket data.

        Returns:
            (is_blocked, speed_scale, reason)
            - is_blocked: True if obstacle is within critical stop distance.
            - speed_scale: Float in [0.0, 1.0] scaling linear speed.
            - reason: Diagnostic text description.
        """
        if not range_data:
            return False, 1.0, "OK"

        front_sensors = [
            ("us_fl_mm", float(range_data.get("us_fl_mm", 2000.0)) / 1000.0),
            ("us_fc_mm", float(range_data.get("us_fc_mm", 2000.0)) / 1000.0),
            ("us_fr_mm", float(range_data.get("us_fr_mm", 2000.0)) / 1000.0),
            ("tof_front_mm", float(range_data.get("tof_front_mm", 2000.0)) / 1000.0),
        ]

        min_front_dist = min(d for _, d in front_sensors if d > 0.01)

        left_clearance = min(
            float(range_data.get("us_l_mm", 2000.0)) / 1000.0,
            float(range_data.get("us_fl_mm", 2000.0)) / 1000.0
        )
        right_clearance = min(
            float(range_data.get("us_r_mm", 2000.0)) / 1000.0,
            float(range_data.get("us_fr_mm", 2000.0)) / 1000.0
        )

        # Critical Safety Stop
        if min_front_dist <= self.safety_stop_m:
            safer_dir = "LEFT" if left_clearance > right_clearance else "RIGHT"
            if left_clearance <= self.safety_stop_m and right_clearance <= self.safety_stop_m:
                safer_dir = "TRAPPED"
            return True, 0.0, f"OBSTACLE_CRITICAL ({min_front_dist:.2f}m) - SAFER: {safer_dir}"

        # Dynamic Slowdown
        if min_front_dist < self.slowdown_m:
            ratio = (min_front_dist - self.safety_stop_m) / (self.slowdown_m - self.safety_stop_m)
            speed_scale = max(0.2, min(1.0, ratio))
            return False, speed_scale, f"SLOWDOWN ({min_front_dist:.2f}m)"

        return False, 1.0, "CLEAR"
