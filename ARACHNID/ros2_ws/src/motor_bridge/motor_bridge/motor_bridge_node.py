"""ARACHNID Motor Bridge Node - Person A (Robotics & Autonomy).

Subscribes to `/cmd_vel` and `/emergency_stop`, converts velocity commands
to differential motor setpoints, enforces 500ms safety watchdog timeout,
and transmits commands over serial to Drive ESP32 adhering to Contract v1.0.0.
"""

from typing import Any, Dict, Optional
import json
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from motor_bridge.packet_builder import PacketBuilder
from motor_bridge.watchdog import MotorWatchdog


class MotorBridgeNode(Node):
    """ROS2 Node managing velocity command dispatch to physical drive hardware."""

    def __init__(self):
        super().__init__("motor_bridge_node")

        # Declare configurable parameters
        self.declare_parameter("drive_port", "COM5")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("wheel_base_m", 0.28)
        self.declare_parameter("wheel_radius_m", 0.05)
        self.declare_parameter("watchdog_timeout_s", 0.50)
        self.declare_parameter("mock_mode", False)
        self.declare_parameter("timer_rate_hz", 20.0)

        drive_port = str(self.get_parameter("drive_port").value)
        baudrate = int(self.get_parameter("baudrate").value)
        wheel_base = float(self.get_parameter("wheel_base_m").value)
        wheel_radius = float(self.get_parameter("wheel_radius_m").value)
        watchdog_timeout = float(self.get_parameter("watchdog_timeout_s").value)
        mock_mode = bool(self.get_parameter("mock_mode").value)
        rate = float(self.get_parameter("timer_rate_hz").value)

        # Core submodules
        self.packet_builder = PacketBuilder(wheel_base_m=wheel_base, wheel_radius_m=wheel_radius)
        self.watchdog = MotorWatchdog(timeout_s=watchdog_timeout)

        # Publisher for raw serial string commands
        self.serial_pub = self.create_publisher(String, "/motor_commands_serial", 10)

        # State setpoints
        self.current_cmd_id = "INIT-000"
        self.current_linear_mps = 0.0
        self.current_angular_rads = 0.0
        self.current_source = "AUTONOMY"
        self.is_emergency_stop = False

        # Subscribers
        self.create_subscription(
            String,
            "/cmd_vel",
            self.cmd_vel_callback,
            10,
        )

        self.create_subscription(
            String,
            "/emergency_stop",
            self.emergency_stop_callback,
            10,
        )

        # Publishers
        self.error_pub = self.create_publisher(
            String,
            "/robot_errors",
            10,
        )

        # Periodic transmission loop (20Hz)
        period = 1.0 / max(1.0, rate)
        self.timer = self.create_timer(period, self.control_loop)

        self.get_logger().info(
            f"Motor Bridge Node started at {rate} Hz (Port: {drive_port}, Baud: {baudrate}, Watchdog: {watchdog_timeout}s)"
        )

    def cmd_vel_callback(self, msg: String) -> None:
        """Handle incoming /cmd_vel VelocityCommand."""
        if self.is_emergency_stop:
            return

        try:
            cmd = json.loads(msg.data)
            self.current_cmd_id = str(cmd.get("command_id", "CMD-UNKNOWN"))
            self.current_linear_mps = float(cmd.get("linear_mps", 0.0))
            self.current_angular_rads = float(cmd.get("angular_rads", 0.0))
            self.current_source = str(cmd.get("source", "AUTONOMY"))
            self.watchdog.kick()
        except Exception as e:
            self.get_logger().warn(f"Failed to parse /cmd_vel message: {e}")

    def emergency_stop_callback(self, msg: String) -> None:
        """Handle immediate /emergency_stop trigger."""
        try:
            data = json.loads(msg.data)
            stop_req = bool(data.get("stop", True))
        except Exception:
            stop_req = True

        if stop_req:
            self.is_emergency_stop = True
            self.watchdog.trigger_emergency_latch()
            self.current_linear_mps = 0.0
            self.current_angular_rads = 0.0

            msg = String()
            msg.data = self.packet_builder.build_string_packet(0.0, 0.0)
            self.serial_pub.publish(msg)
            self.get_logger().error("Emergency Stop engaged in Motor Bridge!")

    def control_loop(self) -> None:
        """Periodic 20Hz loop enforcing safety watchdog and dispatching serial packets."""
        if self.is_emergency_stop:
            msg = String()
            msg.data = self.packet_builder.build_string_packet(0.0, 0.0)
            self.serial_pub.publish(msg)
            return

        # Check safety watchdog
        if self.watchdog.check():
            if not self.watchdog.is_latched:
                elapsed = self.watchdog.get_elapsed_time()
                self.get_logger().warn(f"Watchdog timeout ({elapsed:.2f}s). Stopping motors.")
                self.publish_error(
                    component="motor_bridge",
                    code="WATCHDOG_TIMEOUT",
                    severity="WARNING",
                    message=f"No /cmd_vel received for {elapsed:.2f}s. Motors halted.",
                )
            self.current_linear_mps = 0.0
            self.current_angular_rads = 0.0
            cmd_str = self.packet_builder.build_string_packet(0.0, 0.0)
        else:
            cmd_str = self.packet_builder.build_string_packet(
                self.current_linear_mps,
                self.current_angular_rads,
            )

        msg = String()
        msg.data = cmd_str
        self.serial_pub.publish(msg)

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

    def destroy_node(self) -> None:
        if hasattr(self, "serial_pub"):
            msg = String()
            msg.data = self.packet_builder.build_string_packet(0.0, 0.0)
            self.serial_pub.publish(msg)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
