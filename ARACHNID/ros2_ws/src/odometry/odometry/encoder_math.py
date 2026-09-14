"""ARACHNID Wheel Odometry Kinematics.

Differential drive mathematical model for track tick deltas, arc integration,
and linear/angular velocity calculations.
"""

from typing import Tuple
import math


def normalize_angle(angle: float) -> float:
    """Normalize an angle to [-pi, pi]."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class EncoderMath:
    """Differential drive wheel odometry calculations."""

    def __init__(
        self,
        wheel_radius_m: float = 0.05,
        wheel_base_m: float = 0.28,
        ticks_per_rev: int = 360,
    ):
        self.wheel_radius = float(wheel_radius_m)
        self.wheel_base = float(wheel_base_m)
        self.ticks_per_rev = max(1, int(ticks_per_rev))

        self.last_left_ticks = 0
        self.last_right_ticks = 0
        self.first_reading = True

    def reset(self, left_ticks: int = 0, right_ticks: int = 0) -> None:
        self.last_left_ticks = left_ticks
        self.last_right_ticks = right_ticks
        self.first_reading = False

    def ticks_to_distance(self, delta_ticks: int) -> float:
        """Convert delta encoder ticks to linear travel in metres."""
        circumference = 2.0 * math.pi * self.wheel_radius
        return (delta_ticks / float(self.ticks_per_rev)) * circumference

    def update_pose(
        self,
        current_left_ticks: int,
        current_right_ticks: int,
        current_pose: Tuple[float, float, float],
        dt: float = 0.05,
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float]]:
        """Updates pose (x, y, yaw) and computes (linear_vel, angular_vel).

        Args:
            current_left_ticks: Total cumulative left wheel ticks.
            current_right_ticks: Total cumulative right wheel ticks.
            current_pose: Current (x_m, y_m, yaw_rad).
            dt: Time step in seconds.

        Returns:
            ((new_x, new_y, new_yaw), (linear_velocity_mps, angular_velocity_rads))
        """
        x, y, yaw = current_pose

        if self.first_reading:
            self.last_left_ticks = current_left_ticks
            self.last_right_ticks = current_right_ticks
            self.first_reading = False
            return (x, y, yaw), (0.0, 0.0)

        delta_left = current_left_ticks - self.last_left_ticks
        delta_right = current_right_ticks - self.last_right_ticks

        self.last_left_ticks = current_left_ticks
        self.last_right_ticks = current_right_ticks

        dist_left = self.ticks_to_distance(delta_left)
        dist_right = self.ticks_to_distance(delta_right)

        delta_distance = (dist_left + dist_right) / 2.0
        delta_yaw = (dist_right - dist_left) / self.wheel_base

        # Arc integration
        if abs(delta_yaw) < 1e-6:
            new_x = x + delta_distance * math.cos(yaw + delta_yaw / 2.0)
            new_y = y + delta_distance * math.sin(yaw + delta_yaw / 2.0)
        else:
            radius = delta_distance / delta_yaw
            new_x = x + radius * (math.sin(yaw + delta_yaw) - math.sin(yaw))
            new_y = y - radius * (math.cos(yaw + delta_yaw) - math.cos(yaw))

        new_yaw = normalize_angle(yaw + delta_yaw)

        dt_safe = max(1e-4, dt)
        linear_vel = delta_distance / dt_safe
        angular_vel = delta_yaw / dt_safe

        return (new_x, new_y, new_yaw), (linear_vel, angular_vel)