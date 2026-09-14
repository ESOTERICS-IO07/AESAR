"""ARACHNID IMU + Wheel Odometry Heading Fusion.

Fuses high-frequency gyroscope integration with low-frequency wheel odometry heading.
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
    """Calculates shortest signed angular distance from one angle to another."""
    diff = normalize_angle(to_angle - from_angle)
    return diff


class IMUFusion:
    """Complementary filter for IMU gyroscope and wheel encoder heading."""

    def __init__(self, alpha: float = 0.95):
        # alpha is weight for integrated gyro, (1-alpha) for encoder heading
        self.alpha = max(0.0, min(1.0, float(alpha)))
        self.fused_yaw = 0.0
        self.initialized = False

    def reset(self, initial_yaw: float = 0.0) -> None:
        self.fused_yaw = normalize_angle(initial_yaw)
        self.initialized = True

    def update(self, gyro_z_rads: float, encoder_yaw_rad: float, dt: float = 0.05) -> float:
        """Update fused heading.

        Args:
            gyro_z_rads: Yaw angular velocity from IMU in rad/s.
            encoder_yaw_rad: Heading from wheel odometry in radians.
            dt: Time step in seconds.

        Returns:
            fused_yaw in radians in [-pi, pi].
        """
        if not self.initialized:
            self.fused_yaw = normalize_angle(encoder_yaw_rad)
            self.initialized = True
            return self.fused_yaw

        # Integrate gyroscope
        gyro_predicted_yaw = normalize_angle(self.fused_yaw + gyro_z_rads * dt)

        # Complementary fusion using angular error to avoid 2*pi wrap jump
        diff = shortest_angular_distance(gyro_predicted_yaw, encoder_yaw_rad)
        self.fused_yaw = normalize_angle(gyro_predicted_yaw + (1.0 - self.alpha) * diff)

        return self.fused_yaw