"""ARACHNID Frontier Exploration Manager - Person A (Robotics & Autonomy).

Processes incoming occupancy maps, identifies exploration frontiers,
and publishes ranked candidate targets to `/frontiers` adhering to Contract v1.0.0.
"""

from typing import Any, Dict, Optional
import json
import time

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from exploration.frontier_detector import FrontierDetector
from exploration.frontier_selector import FrontierSelector


class ExplorationManager(Node):
    """ROS2 Node managing autonomous frontier exploration."""

    def __init__(self):
        super().__init__("exploration_manager")

        self.declare_parameter("min_cluster_size", 2)
        self.declare_parameter("max_frontiers_to_publish", 10)
        self.declare_parameter("publish_rate_hz", 2.0)

        self.min_cluster_size = int(self.get_parameter("min_cluster_size").value)
        self.max_frontiers = int(self.get_parameter("max_frontiers_to_publish").value)
        rate = float(self.get_parameter("publish_rate_hz").value)

        self.grid: Optional[np.ndarray] = None
        self.latest_pose: Optional[Dict[str, Any]] = None

        # Subscribers
        self.create_subscription(
            String,
            "/map",
            self.map_callback,
            10,
        )

        self.create_subscription(
            String,
            "/robot_pose",
            self.pose_callback,
            10,
        )

        # Publisher
        self.frontier_pub = self.create_publisher(
            String,
            "/frontiers",
            10,
        )

        # Timer
        period = 1.0 / max(0.5, rate)
        self.timer = self.create_timer(period, self.publish_frontiers)

        self.get_logger().info(
            f"Exploration Manager started at {rate} Hz (MinCluster: {self.min_cluster_size})"
        )

    def map_callback(self, msg: String) -> None:
        try:
            packet = json.loads(msg.data)
            height = int(packet["height"])
            width = int(packet["width"])
            self.grid = np.array(packet["data"], dtype=np.int8).reshape((height, width))
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /map message: {e}")

    def pose_callback(self, msg: String) -> None:
        try:
            self.latest_pose = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /robot_pose message: {e}")

    def publish_frontiers(self) -> None:
        if self.grid is None or self.latest_pose is None:
            return

        robot_pos = (
            float(self.latest_pose.get("x_m", 0.0)),
            float(self.latest_pose.get("y_m", 0.0)),
        )

        # 1. Detect individual frontier cells
        frontier_cells = FrontierDetector.detect_frontier_cells(self.grid)

        # 2. Cluster frontier cells
        clusters = FrontierDetector.cluster_frontiers(
            frontier_cells=frontier_cells,
            min_cluster_size=self.min_cluster_size,
        )

        # 3. Score and format candidates
        frontiers_list = FrontierSelector.select_frontiers(
            clusters=clusters,
            robot_world_pose=robot_pos,
            max_frontiers_to_publish=self.max_frontiers,
        )

        packet = {
            "timestamp_ms": int(time.time() * 1000),
            "frontiers": frontiers_list,
        }

        msg = String()
        msg.data = json.dumps(packet)
        self.frontier_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ExplorationManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()