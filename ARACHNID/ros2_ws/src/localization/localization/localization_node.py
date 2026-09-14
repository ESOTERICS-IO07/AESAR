"""ARACHNID Localization Node - Person A (Robotics & Autonomy).

Fuses odometry and IMU angular rate to estimate robot pose in the map frame,
publishing to `/robot_pose` adhering to Contract v1.0.0.
"""

from typing import Any, Dict, Optional
import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from localization.complementary_filter import ComplementaryFilter
from localization.pose_estimator import PoseEstimator


class LocalizationNode(Node):
    """ROS2 Node for robot localization and pose publishing."""

    def __init__(self):
        super().__init__("localization_node")

        self.declare_parameter("frame_id", "map")
        self.declare_parameter("alpha_heading", 0.95)
        self.declare_parameter("publish_rate_hz", 20.0)

        frame_id = str(self.get_parameter("frame_id").value)
        alpha = float(self.get_parameter("alpha_heading").value)
        rate = float(self.get_parameter("publish_rate_hz").value)

        self.filter = ComplementaryFilter(alpha=alpha)
        self.pose_estimator = PoseEstimator(frame=frame_id)

        self.latest_odom: Optional[Dict[str, Any]] = None
        self.latest_imu: Optional[Dict[str, Any]] = None
        self.last_update_time = time.time()
        self.last_odom_rx_time = 0.0

        # Subscribers
        self.create_subscription(
            String,
            "/odom",
            self.odom_callback,
            10,
        )

        self.create_subscription(
            String,
            "/imu/data",
            self.imu_callback,
            10,
        )

        # Publisher
        self.pose_pub = self.create_publisher(
            String,
            "/robot_pose",
            10,
        )

        # Timer
        period = 1.0 / max(1.0, rate)
        self.timer = self.create_timer(period, self.publish_pose)

        self.get_logger().info(
            f"Localization Node started at {rate} Hz (frame: {frame_id}, alpha: {alpha})"
        )

    def odom_callback(self, msg: String) -> None:
        try:
            self.latest_odom = json.loads(msg.data)
            self.last_odom_rx_time = time.time()
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /odom message: {e}")

    def imu_callback(self, msg: String) -> None:
        try:
            self.latest_imu = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /imu/data message: {e}")

    def publish_pose(self) -> None:
        if self.latest_odom is None:
            return

        now = time.time()
        dt = max(1e-4, now - self.last_update_time)
        self.last_update_time = now

        gyro_z = 0.0
        if self.latest_imu is not None:
            gyro_z = float(self.latest_imu.get("gyro_z_rads", 0.0))

        odom_yaw = float(self.latest_odom.get("yaw_rad", 0.0))

        fused_yaw = self.filter.update(
            gyro_z_rads=gyro_z,
            odom_yaw_rad=odom_yaw,
            dt=dt,
        )

        age = now - self.last_odom_rx_time if self.last_odom_rx_time > 0 else 0.0
        pose_packet = self.pose_estimator.update(
            odom_packet=self.latest_odom,
            fused_yaw=fused_yaw,
            last_update_age_s=age,
        )

        msg = String()
        msg.data = json.dumps(pose_packet)
        self.pose_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LocalizationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()