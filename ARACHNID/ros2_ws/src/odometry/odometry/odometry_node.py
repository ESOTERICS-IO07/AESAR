"""ARACHNID Odometry Node - Person A (Robotics & Autonomy).

Fuses wheel encoder data and IMU gyroscope rates into differential drive odometry
and publishes `/odom` adhering to Contract v1.0.0.
"""

from typing import Tuple
import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from odometry.encoder_math import EncoderMath, normalize_angle
from odometry.imu_fusion import IMUFusion


class OdometryNode(Node):
    """ROS2 Node calculating and publishing differential drive odometry."""

    def __init__(self):
        super().__init__("odometry_node")

        # Declare configurable parameters
        self.declare_parameter("wheel_radius_m", 0.05)
        self.declare_parameter("wheel_base_m", 0.28)
        self.declare_parameter("encoder_ticks_per_rev", 360)
        self.declare_parameter("alpha_imu", 0.95)
        self.declare_parameter("publish_rate_hz", 20.0)

        wheel_radius = float(self.get_parameter("wheel_radius_m").value)
        wheel_base = float(self.get_parameter("wheel_base_m").value)
        ticks_per_rev = int(self.get_parameter("encoder_ticks_per_rev").value)
        alpha = float(self.get_parameter("alpha_imu").value)
        rate = float(self.get_parameter("publish_rate_hz").value)

        self.encoder_math = EncoderMath(
            wheel_radius_m=wheel_radius,
            wheel_base_m=wheel_base,
            ticks_per_rev=ticks_per_rev,
        )
        self.imu_fusion = IMUFusion(alpha=alpha)

        # State variables
        self.left_ticks = 0
        self.right_ticks = 0
        self.gyro_z_rads = 0.0
        self.pose: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (x, y, yaw)
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0

        self.last_update_time = time.time()

        # Subscribers
        self.create_subscription(
            String,
            "/sensors/range",
            self.range_callback,
            10,
        )

        self.create_subscription(
            String,
            "/imu/data",
            self.imu_callback,
            10,
        )

        # Publisher
        self.odom_pub = self.create_publisher(
            String,
            "/odom",
            10,
        )

        # Periodic timer
        period = 1.0 / max(1.0, rate)
        self.timer = self.create_timer(period, self.publish_odometry)

        self.get_logger().info(
            f"Odometry Node started at {rate} Hz. Radius: {wheel_radius}m, Base: {wheel_base}m"
        )

    def range_callback(self, msg: String) -> None:
        """Parse incoming sensor data for encoder ticks if present."""
        try:
            data = json.loads(msg.data)
            # Support both tick keys for robustness
            if "left_ticks" in data:
                self.left_ticks = int(data["left_ticks"])
            elif "enc_left_ticks" in data:
                self.left_ticks = int(data["enc_left_ticks"])

            if "right_ticks" in data:
                self.right_ticks = int(data["right_ticks"])
            elif "enc_right_ticks" in data:
                self.right_ticks = int(data["enc_right_ticks"])
        except Exception as e:
            self.get_logger().warn(f"Failed to parse range message for odometry: {e}")

    def imu_callback(self, msg: String) -> None:
        """Parse incoming IMU data for z-axis angular velocity."""
        try:
            data = json.loads(msg.data)
            self.gyro_z_rads = float(data.get("gyro_z_rads", 0.0))
        except Exception as e:
            self.get_logger().warn(f"Failed to parse IMU message for odometry: {e}")

    def publish_odometry(self) -> None:
        """Calculate kinematics, fuse IMU heading, and publish OdometryPacket."""
        now = time.time()
        dt = max(1e-4, now - self.last_update_time)
        self.last_update_time = now

        # Update pose from wheel encoders
        (new_x, new_y, enc_yaw), (v_lin, v_ang) = self.encoder_math.update_pose(
            current_left_ticks=self.left_ticks,
            current_right_ticks=self.right_ticks,
            current_pose=self.pose,
            dt=dt,
        )

        # Fuse IMU gyro with encoder heading
        fused_yaw = self.imu_fusion.update(
            gyro_z_rads=self.gyro_z_rads,
            encoder_yaw_rad=enc_yaw,
            dt=dt,
        )

        self.pose = (new_x, new_y, fused_yaw)
        self.linear_velocity = v_lin
        # Use fused angular velocity if gyro is available
        self.angular_velocity = self.gyro_z_rads if abs(self.gyro_z_rads) > 1e-4 else v_ang

        odom_packet = {
            "timestamp_ms": int(time.time() * 1000),
            "x_m": round(self.pose[0], 3),
            "y_m": round(self.pose[1], 3),
            "yaw_rad": round(self.pose[2], 3),
            "linear_velocity_mps": round(self.linear_velocity, 3),
            "angular_velocity_rads": round(self.angular_velocity, 3),
            "left_ticks": int(self.left_ticks),
            "right_ticks": int(self.right_ticks),
        }

        msg = String()
        msg.data = json.dumps(odom_packet)
        self.odom_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()