"""ARACHNID Occupancy Grid Mapping Node - Person A (Robotics & Autonomy).

Builds and maintains a 2D occupancy grid from ultrasonic and ToF range sensors,
performing raycasting in the world map frame and publishing to `/map` according to Contract v1.0.0.
"""

from typing import Any, Dict, List, Optional
import json
import time

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from mapping.grid_utils import (
    HEIGHT,
    ORIGIN_X,
    ORIGIN_Y,
    RESOLUTION,
    WIDTH,
    create_grid,
    set_free,
    set_occupied,
    world_to_grid,
)
from mapping.ray_casting import (
    bresenham,
    sensor_endpoint,
    transform_sensor_to_world,
)


class OccupancyGridNode(Node):
    """ROS2 Node for 2D Occupancy Grid Mapping."""

    def __init__(self):
        super().__init__("occupancy_grid_node")

        self.declare_parameter("min_range_m", 0.02)
        self.declare_parameter("max_range_m", 2.50)
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("us_fc_mount_x_m", 0.16)

        self.min_range_m = float(self.get_parameter("min_range_m").value)
        self.max_range_m = float(self.get_parameter("max_range_m").value)
        rate = float(self.get_parameter("publish_rate_hz").value)
        us_fc_x = float(self.get_parameter("us_fc_mount_x_m").value)

        self.grid = create_grid()
        self.latest_pose: Optional[Dict[str, Any]] = None

        # Sensor mount geometry relative to robot base [mount_x, mount_y, mount_yaw]
        self.sensor_mounts = {
            "us_fl_mm": (0.15, 0.08, 0.349066),    # Front-Left: +20 deg
            "us_fc_mm": (us_fc_x, 0.00, 0.0),      # Front-Center: 0 deg (Provisional)
            "us_fr_mm": (0.15, -0.08, -0.349066),  # Front-Right: -20 deg
            "us_l_mm": (0.00, 0.12, 1.570796),     # Left: +90 deg
            "us_r_mm": (0.00, -0.12, -1.570796),   # Right: -90 deg
            "tof_front_mm": (0.16, 0.00, 0.0),     # Front ToF: 0 deg
        }

        # Subscribers
        self.create_subscription(
            String,
            "/robot_pose",
            self.pose_callback,
            10,
        )

        self.create_subscription(
            String,
            "/sensors/range",
            self.range_callback,
            10,
        )

        # Publisher
        self.map_pub = self.create_publisher(
            String,
            "/map",
            10,
        )

        # Timer
        period = 1.0 / max(1.0, rate)
        self.timer = self.create_timer(period, self.publish_map)

        self.get_logger().info(
            f"Occupancy Grid Node started at {rate} Hz (Resolution: {RESOLUTION}m, Grid: {WIDTH}x{HEIGHT})"
        )

    def pose_callback(self, msg: String) -> None:
        try:
            self.latest_pose = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /robot_pose: {e}")

    def range_callback(self, msg: String) -> None:
        if self.latest_pose is None:
            return

        try:
            range_data = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /sensors/range: {e}")
            return

        robot_x = float(self.latest_pose.get("x_m", 0.0))
        robot_y = float(self.latest_pose.get("y_m", 0.0))
        robot_yaw = float(self.latest_pose.get("yaw_rad", 0.0))

        # Clear cell directly under the robot
        rgx, rgy = world_to_grid(robot_x, robot_y)
        set_free(self.grid, rgx, rgy)

        for sensor_key, mount_info in self.sensor_mounts.items():
            if sensor_key not in range_data:
                continue

            raw_dist_mm = float(range_data[sensor_key])
            dist_m = raw_dist_mm / 1000.0

            # Ignore readings below min threshold (noise/error)
            if dist_m < self.min_range_m:
                continue

            mount_x, mount_y, mount_yaw = mount_info
            sensor_x, sensor_y, beam_yaw = transform_sensor_to_world(
                robot_x=robot_x,
                robot_y=robot_y,
                robot_yaw=robot_yaw,
                mount_x=mount_x,
                mount_y=mount_y,
                mount_yaw=mount_yaw,
            )

            is_obstacle = dist_m < self.max_range_m
            ray_dist = min(dist_m, self.max_range_m)

            end_x, end_y = sensor_endpoint(
                sensor_x=sensor_x,
                sensor_y=sensor_y,
                beam_yaw=beam_yaw,
                distance_m=ray_dist,
            )

            gx0, gy0 = world_to_grid(sensor_x, sensor_y)
            gx1, gy1 = world_to_grid(end_x, end_y)

            ray_cells = bresenham(gx0, gy0, gx1, gy1)

            if is_obstacle:
                # Mark intermediate cells free
                for cx, cy in ray_cells[:-1]:
                    self.update_cell(cx, cy, free=True)
                # Mark endpoint occupied
                if ray_cells:
                    last_cx, last_cy = ray_cells[-1]
                    self.update_cell(last_cx, last_cy, free=False)
            else:
                # All cells free (no obstacle detected within range)
                for cx, cy in ray_cells:
                    self.update_cell(cx, cy, free=True)

    def update_cell(self, cx: int, cy: int, free: bool) -> None:
        if not (0 <= cx < WIDTH and 0 <= cy < HEIGHT):
            return
        
        current = self.grid[cy, cx]
        if free:
            if current == -1:
                self.grid[cy, cx] = 0
            elif current > 0:
                self.grid[cy, cx] = max(0, current - 20)
        else:
            if current == -1:
                self.grid[cy, cx] = 100
            else:
                self.grid[cy, cx] = min(100, current + 40)

    def publish_map(self) -> None:
        """Publish OccupancyGrid packet matching Contract v1.0.0."""
        packet = {
            "timestamp_ms": int(time.time() * 1000),
            "frame": "map",
            "resolution_m_per_cell": RESOLUTION,
            "width": WIDTH,
            "height": HEIGHT,
            "origin_x_m": ORIGIN_X,
            "origin_y_m": ORIGIN_Y,
            "data": self.grid.flatten().tolist(),
        }

        msg = String()
        msg.data = json.dumps(packet)
        self.map_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OccupancyGridNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()