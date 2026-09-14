"""ARACHNID Localization Complementary Filter.

Fuses high-rate IMU angular rate integration with wheel odometry heading.
"""

import math


def normalize_angle(angle: float) -> float:
    """Normalize an angle to [-pi, pi]."""
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def shortest_angular_distance(from_angle: float, to_angle: float) -> float:
    """Calculates shortest signed angular distance between angles."""
    return normalize_angle(to_angle - from_angle)


class ComplementaryFilter:
    """Fuses IMU gyroscope rate with odometry heading."""

    def __init__(self, alpha: float = 0.95):
        self.alpha = max(0.0, min(1.0, float(alpha)))
        self.fused_yaw = 0.0
        self.initialized = False

    def reset(self, initial_yaw: float = 0.0) -> None:
        self.fused_yaw = normalize_angle(initial_yaw)
        self.initialized = True

    def update(self, gyro_z_rads: float, odom_yaw_rad: float, dt: float = 0.05) -> float:
        """Update fused yaw angle.

        Args:
            gyro_z_rads: IMU z-axis angular velocity in rad/s.
            odom_yaw_rad: Odometry heading in radians.
            dt: Time delta in seconds.

        Returns:
            fused yaw in radians [-pi, pi].
        """
        if not self.initialized:
            self.fused_yaw = normalize_angle(odom_yaw_rad)
            self.initialized = True
            return self.fused_yaw

        # Integrate IMU angular velocity
        predicted_yaw = normalize_angle(self.fused_yaw + gyro_z_rads * dt)

        # Complementary correction towards odometry heading
        err = shortest_angular_distance(predicted_yaw, odom_yaw_rad)
        self.fused_yaw = normalize_angle(predicted_yaw + (1.0 - self.alpha) * err)

        return self.fused_yaw