"""ARACHNID Pure Pursuit Velocity Controller.

Calculates smooth linear and angular velocity commands to follow planned waypoints
while adhering strictly to kinematics limits and Contract v1.0.0.
"""

from typing import Any, Dict, List, Optional, Tuple
import math
import time

from odometry.encoder_math import normalize_angle


class VelocityController:
    """Proportional Pure Pursuit path tracker."""

    def __init__(
        self,
        max_linear_mps: float = 0.35,
        max_angular_rads: float = 1.05,
        goal_tolerance_m: float = 0.15,
        lookahead_distance_m: float = 0.30,
        kp_angular: float = 2.0,
    ):
        self.max_linear = float(max_linear_mps)
        self.max_angular = float(max_angular_rads)
        self.goal_tolerance = float(goal_tolerance_m)
        self.lookahead = float(lookahead_distance_m)
        self.kp_ang = float(kp_angular)
        self.command_seq = 0

    def compute_command(
        self,
        current_pose: Tuple[float, float, float],
        path_points: List[Dict[str, float]],
        speed_scale: float = 1.0,
        source: str = "AUTONOMY",
    ) -> Tuple[Dict[str, Any], bool]:
        """Compute next velocity command for the given path.

        Args:
            current_pose: (x_m, y_m, yaw_rad).
            path_points: List of waypoints [{"x_m": ..., "y_m": ..., "yaw_rad": ...}].
            speed_scale: Multiplier from obstacle avoidance in [0.0, 1.0].
            source: Command origin identifier ("AUTONOMY", "MANUAL", etc.).

        Returns:
            (VelocityCommand dict, is_goal_reached)
        """
        self.command_seq += 1
        rx, ry, ryaw = current_pose

        if not path_points:
            return self._build_stop_command(source=source), True

        goal_point = path_points[-1]
        dist_to_goal = math.hypot(goal_point["x_m"] - rx, goal_point["y_m"] - ry)

        # Check if destination reached
        if dist_to_goal <= self.goal_tolerance:
            return self._build_stop_command(source=source), True

        # Find lookahead target point along path
        target_point = path_points[0]
        for pt in path_points:
            d = math.hypot(pt["x_m"] - rx, pt["y_m"] - ry)
            if d >= self.lookahead:
                target_point = pt
                break
            target_point = pt

        # Compute heading error to target waypoint
        desired_yaw = math.atan2(target_point["y_m"] - ry, target_point["x_m"] - rx)
        heading_err = normalize_angle(desired_yaw - ryaw)

        # Angular velocity proportional to heading error
        w = max(-self.max_angular, min(self.max_angular, self.kp_ang * heading_err))

        # Linear velocity scaled down if heading error is large or obstacle near
        alignment_factor = max(0.0, math.cos(heading_err))
        v = self.max_linear * alignment_factor * max(0.0, min(1.0, speed_scale))

        # Ensure minimal forward movement if aligned
        if abs(heading_err) < 0.2 and v < 0.05 and speed_scale > 0.3:
            v = 0.08

        cmd = {
            "command_id": f"CMD-{self.command_seq:06d}",
            "timestamp_ms": int(time.time() * 1000),
            "linear_mps": round(v, 3),
            "angular_rads": round(w, 3),
            "source": source,
        }

        return cmd, False

    def _build_stop_command(self, source: str = "AUTONOMY") -> Dict[str, Any]:
        return {
            "command_id": f"CMD-{self.command_seq:06d}",
            "timestamp_ms": int(time.time() * 1000),
            "linear_mps": 0.0,
            "angular_rads": 0.0,
            "source": source,
        }
