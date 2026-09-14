"""ARACHNID Autonomous Path Planner & Navigation Node - Person A (Robotics & Autonomy).

Coordinates frontier selection, A* path planning, reactive obstacle avoidance,
pure pursuit path following, and emergency stop enforcement strictly adhering to Contract v1.0.0.
"""

from typing import Any, Dict, List, Optional
import json
import time

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from navigation.astar import AStarPlanner
from navigation.obstacle_avoidance import ObstacleAvoidance
from navigation.velocity_controller import VelocityController


class NavigationPlannerNode(Node):
    """ROS2 Node for autonomous navigation, planning, and control."""

    def __init__(self):
        super().__init__("planner_node")

        # Declare configurable parameters
        self.declare_parameter("max_linear_speed_mps", 0.35)
        self.declare_parameter("max_angular_speed_rads", 1.05)
        self.declare_parameter("safety_stop_distance_m", 0.18)
        self.declare_parameter("slowdown_distance_m", 0.40)
        self.declare_parameter("goal_tolerance_m", 0.15)
        self.declare_parameter("obstacle_inflation_cells", 3)
        self.declare_parameter("control_rate_hz", 20.0)

        max_v = float(self.get_parameter("max_linear_speed_mps").value)
        max_w = float(self.get_parameter("max_angular_speed_rads").value)
        safety_dist = float(self.get_parameter("safety_stop_distance_m").value)
        slowdown_dist = float(self.get_parameter("slowdown_distance_m").value)
        goal_tol = float(self.get_parameter("goal_tolerance_m").value)
        inflation_cells = int(self.get_parameter("obstacle_inflation_cells").value)
        rate = float(self.get_parameter("control_rate_hz").value)

        # Core autonomy modules
        self.planner = AStarPlanner(inflation_radius_cells=inflation_cells)
        self.avoidance = ObstacleAvoidance(
            safety_stop_distance_m=safety_dist,
            slowdown_distance_m=slowdown_dist,
        )
        self.controller = VelocityController(
            max_linear_mps=max_v,
            max_angular_rads=max_w,
            goal_tolerance_m=goal_tol,
        )

        # State variables
        self.robot_mode = "AUTONOMOUS"       # DISCONNECTED, IDLE, MANUAL, AUTONOMOUS, PAUSED, EMERGENCY_STOP, ERROR
        self.nav_status = "IDLE"             # IDLE, SELECTING_FRONTIER, PLANNING, NAVIGATING, OBSTACLE_BLOCKED, TARGET_REACHED, NO_PATH, COMPLETE, ERROR
        self.safety_status = "NORMAL"        # NORMAL, WARNING, STOP_REQUESTED, EMERGENCY_STOP, HARDWARE_FAULT
        self.battery_percent = 98.0
        self.emergency_stopped = False

        self.latest_map: Optional[np.ndarray] = None
        self.latest_pose: Optional[Dict[str, Any]] = None
        self.latest_range: Optional[Dict[str, Any]] = None
        self.latest_frontiers: List[Dict[str, Any]] = []

        self.current_target_id: str = ""
        self.current_path: List[Dict[str, float]] = []

        self.last_pose_time = time.time()
        self.last_sensor_time = time.time()
        self.last_pose = (0.0, 0.0, 0.0)
        self.stuck_time_start = None

        # Subscribers
        self.create_subscription(String, "/frontiers", self.frontiers_callback, 10)
        self.create_subscription(String, "/robot_pose", self.pose_callback, 10)
        self.create_subscription(String, "/map", self.map_callback, 10)
        self.create_subscription(String, "/sensors/range", self.range_callback, 10)
        self.create_subscription(String, "/emergency_stop", self.emergency_stop_callback, 10)

        # Publishers
        self.path_pub = self.create_publisher(String, "/planned_path", 10)
        self.cmd_vel_pub = self.create_publisher(String, "/cmd_vel", 10)
        self.state_pub = self.create_publisher(String, "/robot_state", 10)
        self.error_pub = self.create_publisher(String, "/robot_errors", 10)

        # Control loop timer
        period = 1.0 / max(1.0, rate)
        self.timer = self.create_timer(period, self.control_loop)

        self.get_logger().info(f"Planner Node started at {rate} Hz (MaxV: {max_v}m/s, MaxW: {max_w}rad/s)")

    def frontiers_callback(self, msg: String) -> None:
        try:
            packet = json.loads(msg.data)
            self.latest_frontiers = packet.get("frontiers", [])
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /frontiers: {e}")

    def pose_callback(self, msg: String) -> None:
        try:
            self.latest_pose = json.loads(msg.data)
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /robot_pose: {e}")

    def map_callback(self, msg: String) -> None:
        try:
            packet = json.loads(msg.data)
            h = int(packet["height"])
            w = int(packet["width"])
            self.latest_map = np.array(packet["data"], dtype=np.int8).reshape((h, w))
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /map: {e}")

    def range_callback(self, msg: String) -> None:
        try:
            self.latest_range = json.loads(msg.data)
            self.last_sensor_time = time.time()
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /sensors/range: {e}")

    def emergency_stop_callback(self, msg: String) -> None:
        try:
            data = json.loads(msg.data)
            stop_requested = bool(data.get("stop", True))
        except Exception:
            stop_requested = True

        if stop_requested:
            self.emergency_stopped = True
            self.robot_mode = "EMERGENCY_STOP"
            self.safety_status = "EMERGENCY_STOP"
            self.nav_status = "IDLE"
            self.current_path = []
            self.publish_stop_command(source="EMERGENCY_STOP")
            self.publish_error(
                component="navigation",
                code="EMERGENCY_STOP_ACTIVE",
                severity="FATAL",
                message="Emergency stop engaged by operator or safety trigger",
                latched=True,
            )
            self.get_logger().error("EMERGENCY STOP TRIGGERED!")

    def control_loop(self) -> None:
        """Main periodic navigation state machine."""
        if self.emergency_stopped:
            self.publish_stop_command(source="EMERGENCY_STOP")
            self.publish_state()
            return

        if self.latest_pose is None or self.latest_map is None:
            self.publish_state()
            return

        robot_pos = (
            float(self.latest_pose.get("x_m", 0.0)),
            float(self.latest_pose.get("y_m", 0.0)),
        )
        robot_pose_tuple = (
            robot_pos[0],
            robot_pos[1],
            float(self.latest_pose.get("yaw_rad", 0.0)),
        )

        # 0. Check for stale telemetry
        current_time = time.time()
        if current_time - self.last_sensor_time > 0.5:
            self.nav_status = "ERROR"
            self.safety_status = "WARNING"
            self.publish_stop_command(source="AUTONOMY")
            self.publish_error(
                component="navigation",
                code="STALE_TELEMETRY",
                severity="WARNING",
                message="Sensor data is stale (>500ms)",
            )
            self.publish_state()
            return

        # 1. Check reactive obstacle avoidance
        is_blocked = False
        speed_scale = 1.0
        reason = "CLEAR"
        if self.latest_range is not None:
            is_blocked, speed_scale, reason = self.avoidance.evaluate(self.latest_range)

        if is_blocked:
            if "TRAPPED" in reason:
                self.nav_status = "ERROR"
                self.publish_error(
                    component="navigation",
                    code="TRAPPED",
                    severity="ERROR",
                    message="Trapped on multiple sides. Manual intervention required.",
                )
            else:
                self.nav_status = "OBSTACLE_BLOCKED"
            self.safety_status = "WARNING"
            self.publish_stop_command(source="AUTONOMY")
            self.publish_path(status=self.nav_status)
            self.publish_state()
            self.current_path = []
            return
        else:
            self.safety_status = "NORMAL"

        # 2. Plan path if no active path
        if not self.current_path:
            self.select_and_plan(robot_pos)
            self.publish_state()
            return

        # 3. Follow path using velocity controller
        cmd, goal_reached = self.controller.compute_command(
            current_pose=robot_pose_tuple,
            path_points=self.current_path,
            speed_scale=speed_scale,
            source="AUTONOMY",
        )

        # 4. Stuck Detection
        dx = robot_pose_tuple[0] - self.last_pose[0]
        dy = robot_pose_tuple[1] - self.last_pose[1]
        dyaw = robot_pose_tuple[2] - self.last_pose[2]
        dist_moved = (dx**2 + dy**2)**0.5
        
        if abs(cmd["linear_mps"]) > 0.1 or abs(cmd["angular_rads"]) > 0.2:
            if dist_moved < 0.05 and abs(dyaw) < 0.1:
                if self.stuck_time_start is None:
                    self.stuck_time_start = current_time
                elif current_time - self.stuck_time_start > 3.0:
                    self.nav_status = "ERROR"
                    self.publish_error(
                        component="navigation",
                        code="STUCK",
                        severity="ERROR",
                        message="Rover failed to move for 3 seconds despite command.",
                    )
                    self.publish_stop_command(source="AUTONOMY")
                    self.current_path = []
                    self.publish_state()
                    return
            else:
                self.stuck_time_start = None
                self.last_pose = robot_pose_tuple

        if goal_reached:
            self.nav_status = "TARGET_REACHED"
            self.publish_path(status="TARGET_REACHED")
            self.current_path = []
            self.publish_stop_command(source="AUTONOMY")
        else:
            self.nav_status = "NAVIGATING"
            self.publish_cmd_vel(cmd)
            self.publish_path(status="NAVIGATING")

        self.publish_state()

    def select_and_plan(self, robot_pos: tuple) -> None:
        """Select frontier and compute A* path."""
        if not self.latest_frontiers:
            self.nav_status = "IDLE"
            self.publish_stop_command(source="AUTONOMY")
            self.publish_path(status="IDLE")
            return

        self.nav_status = "SELECTING_FRONTIER"

        # Pick selected frontier or top candidate
        target = None
        for f in self.latest_frontiers:
            if f.get("status") == "SELECTED":
                target = f
                break
        if target is None and self.latest_frontiers:
            target = self.latest_frontiers[0]

        if target is None:
            self.nav_status = "COMPLETE"
            return

        self.current_target_id = str(target.get("id", "F-001"))
        goal_pos = (float(target["x_m"]), float(target["y_m"]))

        self.nav_status = "PLANNING"
        path = self.planner.plan_path(
            grid=self.latest_map,
            start_world=robot_pos,
            goal_world=goal_pos,
        )

        if path:
            self.current_path = path
            self.nav_status = "NAVIGATING"
            self.publish_path(status="NAVIGATING")
        else:
            self.nav_status = "NO_PATH"
            self.publish_path(status="NO_PATH")
            self.publish_stop_command(source="AUTONOMY")

    def publish_path(self, status: str) -> None:
        """Publish PathPacket adhering to Contract v1.0.0."""
        packet = {
            "timestamp_ms": int(time.time() * 1000),
            "status": status,
            "target_id": self.current_target_id,
            "points": self.current_path,
        }
        msg = String()
        msg.data = json.dumps(packet)
        self.path_pub.publish(msg)

    def publish_cmd_vel(self, cmd: Dict[str, Any]) -> None:
        """Publish VelocityCommand adhering to Contract v1.0.0."""
        msg = String()
        msg.data = json.dumps(cmd)
        self.cmd_vel_pub.publish(msg)

    def publish_stop_command(self, source: str = "AUTONOMY") -> None:
        """Send zero velocity command."""
        cmd = {
            "command_id": f"CMD-{int(time.time() * 1000) % 1000000:06d}",
            "timestamp_ms": int(time.time() * 1000),
            "linear_mps": 0.0,
            "angular_rads": 0.0,
            "source": source,
        }
        self.publish_cmd_vel(cmd)

    def publish_state(self) -> None:
        """Publish RobotState packet adhering to Contract v1.0.0."""
        state_packet = {
            "timestamp_ms": int(time.time() * 1000),
            "robot_mode": self.robot_mode,
            "nav_status": self.nav_status,
            "safety_status": self.safety_status,
            "battery_percent": round(self.battery_percent, 1),
        }
        msg = String()
        msg.data = json.dumps(state_packet)
        self.state_pub.publish(msg)

    def publish_error(
        self,
        component: str,
        code: str,
        severity: str,
        message: str,
        latched: bool = False,
    ) -> None:
        """Publish RobotError packet adhering to Contract v1.0.0."""
        error_packet = {
            "timestamp_ms": int(time.time() * 1000),
            "component": component,
            "code": code,
            "severity": severity,
            "message": message,
            "latched": latched,
        }
        msg = String()
        msg.data = json.dumps(error_packet)
        self.error_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = NavigationPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
