"""ARACHNID Sensor Interface Node - Person A (Robotics & Autonomy).

Handles serial communication with Sensor ESP32 (via USB or Wi-Fi TCP), parses incoming
telemetry, applies digital filters, validates contract schemas, and publishes
to `/sensors/range`, `/imu/data`, and `/robot_errors`.
"""

from typing import Any, Dict, Optional
import json
import math
import time
import socket

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from sensor_interface.filter import LowPassFilter, MedianFilter, MovingAverageFilter
from sensor_interface.serial_parser import (
    ImuPacketValidator,
    RangePacketValidator,
    SerialParser,
)

try:
    import serial
except ImportError:
    serial = None


class SensorNode(Node):
    """ROS2 Node for acquiring and filtering sensor data via USB or Wi-Fi TCP."""

    def __init__(self):
        super().__init__("sensor_interface_node")

        # Declare configurable parameters
        self.declare_parameter("sensor_port", "COM6")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("use_wifi", True)
        self.declare_parameter("wifi_ip", "192.168.4.1")
        self.declare_parameter("wifi_port", 80)
        self.declare_parameter("read_rate_hz", 20.0)
        self.declare_parameter("mock_mode", False)
        self.declare_parameter("timeout_s", 0.1)

        self.sensor_port = self.get_parameter("sensor_port").value
        self.baudrate = self.get_parameter("baudrate").value
        self.use_wifi = bool(self.get_parameter("use_wifi").value)
        self.wifi_ip = str(self.get_parameter("wifi_ip").value)
        self.wifi_port = int(self.get_parameter("wifi_port").value)
        read_rate = float(self.get_parameter("read_rate_hz").value)
        self.mock_mode = bool(self.get_parameter("mock_mode").value)
        self.timeout_s = float(self.get_parameter("timeout_s").value)

        # Filters
        self.fc_filter = MedianFilter(window_size=5)
        self.fl_filter = MedianFilter(window_size=5)
        self.fr_filter = MedianFilter(window_size=5)
        self.l_filter = MedianFilter(window_size=5)
        self.r_filter = MedianFilter(window_size=5)
        self.tof_filter = MovingAverageFilter(window_size=5)

        self.accel_x_filter = LowPassFilter(alpha=0.25)
        self.accel_y_filter = LowPassFilter(alpha=0.25)
        self.accel_z_filter = LowPassFilter(alpha=0.25)
        self.gyro_x_filter = LowPassFilter(alpha=0.25)
        self.gyro_y_filter = LowPassFilter(alpha=0.25)
        self.gyro_z_filter = LowPassFilter(alpha=0.25)

        # Publishers
        self.range_pub = self.create_publisher(String, "/sensors/range", 10)
        self.imu_pub = self.create_publisher(String, "/imu/data", 10)
        self.error_pub = self.create_publisher(String, "/robot_errors", 10)

        # Connection
        self.serial_conn: Optional[Any] = None
        self.socket_conn: Optional[socket.socket] = None
        self.socket_file: Optional[Any] = None
        self.seq = 0
        
        self._init_connection()

        # Subscriber for shared Serial Bridge (Motor Commands)
        self.create_subscription(
            String,
            "/motor_commands_serial",
            self.motor_cmd_callback,
            10,
        )

        # Timer
        period = 1.0 / max(1.0, read_rate)
        self.timer = self.create_timer(period, self.timer_callback)

        mode_str = f"Wi-Fi ({self.wifi_ip}:{self.wifi_port})" if self.use_wifi else f"USB ({self.sensor_port})"
        self.get_logger().info(
            f"Sensor Interface Node started. Mode: {mode_str}, MockMode: {self.mock_mode}"
        )

    def _init_connection(self) -> None:
        """Initialize connection or switch to mock mode if unavailable."""
        if self.mock_mode:
            self.get_logger().info("Mock mode enabled: Simulating sensor inputs.")
            return

        if self.use_wifi:
            try:
                self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket_conn.settimeout(self.timeout_s)
                self.socket_conn.connect((self.wifi_ip, self.wifi_port))
                self.socket_file = self.socket_conn.makefile('rwb', buffering=0)
                self.get_logger().info(f"Connected to Sensor ESP32 via Wi-Fi at {self.wifi_ip}:{self.wifi_port}")
            except Exception as e:
                self.get_logger().warn(
                    f"Could not connect via Wi-Fi to {self.wifi_ip}:{self.wifi_port}: {e}. Running in fallback mode."
                )
                self.publish_error(
                    component="sensor_interface",
                    code="WIFI_PORT_UNAVAILABLE",
                    severity="WARNING",
                    message=f"Wi-Fi connection failed: {e}",
                )
                self.mock_mode = True
        else:
            if serial is None:
                self.get_logger().warn("pyserial module not found. Falling back to mock mode.")
                self.mock_mode = True
                return

            try:
                self.serial_conn = serial.Serial(
                    port=self.sensor_port,
                    baudrate=self.baudrate,
                    timeout=self.timeout_s,
                )
                self.get_logger().info(f"Connected to Sensor ESP32 on {self.sensor_port}")
            except Exception as e:
                self.get_logger().warn(
                    f"Could not open serial port {self.sensor_port}: {e}. Running in fallback mode."
                )
                self.publish_error(
                    component="sensor_interface",
                    code="SERIAL_PORT_UNAVAILABLE",
                    severity="WARNING",
                    message=f"Serial port {self.sensor_port} failed to open: {e}",
                )
                self.mock_mode = True

    def _reconnect_wifi(self):
        if self.socket_conn:
            try:
                self.socket_conn.close()
            except:
                pass
        self.socket_conn = None
        self.socket_file = None
        
        try:
            self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_conn.settimeout(self.timeout_s)
            self.socket_conn.connect((self.wifi_ip, self.wifi_port))
            self.socket_file = self.socket_conn.makefile('rwb', buffering=0)
            self.get_logger().info("Reconnected to Wi-Fi successfully.")
        except Exception:
            pass

    def motor_cmd_callback(self, msg: String) -> None:
        """Write incoming motor command strings directly to the shared port."""
        if self.mock_mode:
            return

        cmd_bytes = msg.data.encode("utf-8")
        if self.use_wifi and self.socket_file:
            try:
                self.socket_file.write(cmd_bytes)
                self.socket_file.flush()
            except Exception as e:
                self.get_logger().error(f"Failed to write motor command to Wi-Fi socket: {e}")
                self._reconnect_wifi()
        elif not self.use_wifi and self.serial_conn:
            try:
                if hasattr(self.serial_conn, "is_open") and self.serial_conn.is_open:
                    self.serial_conn.write(cmd_bytes)
            except Exception as e:
                self.get_logger().error(f"Failed to write motor command to serial: {e}")

    def timer_callback(self) -> None:
        """Periodic loop to read or simulate sensor packets."""
        self.seq += 1

        if self.mock_mode or (not self.use_wifi and self.serial_conn is None) or (self.use_wifi and self.socket_file is None):
            self.generate_mock_readings()
            if self.use_wifi and not self.mock_mode:
                self._reconnect_wifi()
            return

        self.read_sensor_data()

    def read_sensor_data(self) -> None:
        """Read and parse lines from physical serial port or Wi-Fi socket."""
        try:
            if self.use_wifi and self.socket_file:
                # Read multiple lines quickly if available, handle timeout
                try:
                    while True:
                        raw_line = self.socket_file.readline().decode("utf-8", errors="ignore")
                        if not raw_line:
                            break
                        self._handle_raw_line(raw_line)
                except socket.timeout:
                    pass
                except Exception as e:
                    self.get_logger().error(f"Wi-Fi read error: {e}")
                    self._reconnect_wifi()
                    
            elif not self.use_wifi and self.serial_conn:
                while self.serial_conn.in_waiting:
                    raw_line = self.serial_conn.readline().decode("utf-8", errors="ignore")
                    self._handle_raw_line(raw_line)

        except Exception as e:
            self.get_logger().error(f"Error reading sensor stream: {e}")
            self.publish_error(
                component="sensor_interface",
                code="SENSOR_READ_ERROR",
                severity="ERROR",
                message=str(e),
            )

    def _handle_raw_line(self, raw_line: str) -> None:
        parsed = SerialParser.parse_line(raw_line)
        if not parsed:
            return

        packet_type = parsed.get("type", "")

        if packet_type == "RANGE" or RangePacketValidator.validate(parsed):
            self.process_range_packet(parsed)
        elif packet_type == "IMU" or ImuPacketValidator.validate(parsed):
            self.process_imu_packet(parsed)

    def process_range_packet(self, raw_packet: Dict[str, Any]) -> None:
        """Filter, validate, and publish RangePacket."""
        timestamp_ms = raw_packet.get("timestamp_ms", int(time.time() * 1000))
        seq = raw_packet.get("seq", self.seq)

        filtered_fc = self.fc_filter.update(raw_packet.get("us_fc_mm", 1000.0))
        filtered_fl = self.fl_filter.update(raw_packet.get("us_fl_mm", 1000.0))
        filtered_fr = self.fr_filter.update(raw_packet.get("us_fr_mm", 1000.0))
        filtered_l = self.l_filter.update(raw_packet.get("us_l_mm", 1000.0))
        filtered_r = self.r_filter.update(raw_packet.get("us_r_mm", 1000.0))
        filtered_tof = self.tof_filter.update(raw_packet.get("tof_front_mm", 1000.0))

        sensor_status = raw_packet.get(
            "sensor_status",
            {
                "us_fc": "OK",
                "us_fl": "OK",
                "us_fr": "OK",
                "us_l": "OK",
                "us_r": "OK",
                "tof_front": "OK",
            },
        )

        packet = RangePacketValidator.build_packet(
            seq=seq,
            us_fc_mm=filtered_fc,
            us_fl_mm=filtered_fl,
            us_fr_mm=filtered_fr,
            us_l_mm=filtered_l,
            us_r_mm=filtered_r,
            tof_front_mm=filtered_tof,
            sensor_status=sensor_status,
            timestamp_ms=timestamp_ms,
        )

        msg = String()
        msg.data = json.dumps(packet)
        self.range_pub.publish(msg)

    def process_imu_packet(self, raw_packet: Dict[str, Any]) -> None:
        """Filter, validate, and publish ImuPacket."""
        timestamp_ms = raw_packet.get("timestamp_ms", int(time.time() * 1000))
        seq = raw_packet.get("seq", self.seq)

        filtered_ax = self.accel_x_filter.update(raw_packet.get("accel_x_mps2", 0.0))
        filtered_ay = self.accel_y_filter.update(raw_packet.get("accel_y_mps2", 0.0))
        filtered_az = self.accel_z_filter.update(raw_packet.get("accel_z_mps2", 9.81))
        filtered_gx = self.gyro_x_filter.update(raw_packet.get("gyro_x_rads", 0.0))
        filtered_gy = self.gyro_y_filter.update(raw_packet.get("gyro_y_rads", 0.0))
        filtered_gz = self.gyro_z_filter.update(raw_packet.get("gyro_z_rads", 0.0))

        packet = ImuPacketValidator.build_packet(
            seq=seq,
            accel_x_mps2=filtered_ax,
            accel_y_mps2=filtered_ay,
            accel_z_mps2=filtered_az,
            gyro_x_rads=filtered_gx,
            gyro_y_rads=filtered_gy,
            gyro_z_rads=filtered_gz,
            timestamp_ms=timestamp_ms,
        )

        msg = String()
        msg.data = json.dumps(packet)
        self.imu_pub.publish(msg)

    def generate_mock_readings(self) -> None:
        """Generates realistic synthetic sensor packets when offline."""
        now_ms = int(time.time() * 1000)

        # Mock distance readings
        sim_range_packet = RangePacketValidator.build_packet(
            seq=self.seq,
            us_fc_mm=self.fc_filter.update(860.0),
            us_fl_mm=self.fl_filter.update(850.0 + 10.0 * math.sin(self.seq * 0.1)),
            us_fr_mm=self.fr_filter.update(870.0 + 12.0 * math.cos(self.seq * 0.1)),
            us_l_mm=self.l_filter.update(1200.0),
            us_r_mm=self.r_filter.update(1150.0),
            tof_front_mm=self.tof_filter.update(840.0 + 8.0 * math.sin(self.seq * 0.1)),
            sensor_status={
                "us_fc": "OK",
                "us_fl": "OK",
                "us_fr": "OK",
                "us_l": "OK",
                "us_r": "OK",
                "tof_front": "OK",
            },
            timestamp_ms=now_ms,
        )

        # Mock IMU readings
        sim_imu_packet = ImuPacketValidator.build_packet(
            seq=self.seq,
            accel_x_mps2=self.accel_x_filter.update(0.01 * math.sin(self.seq * 0.05)),
            accel_y_mps2=self.accel_y_filter.update(0.01 * math.cos(self.seq * 0.05)),
            accel_z_mps2=self.accel_z_filter.update(9.806),
            gyro_x_rads=self.gyro_x_filter.update(0.0),
            gyro_y_rads=self.gyro_y_filter.update(0.0),
            gyro_z_rads=self.gyro_z_filter.update(0.0),
            timestamp_ms=now_ms,
        )

        range_msg = String()
        range_msg.data = json.dumps(sim_range_packet)
        self.range_pub.publish(range_msg)

        imu_msg = String()
        imu_msg.data = json.dumps(sim_imu_packet)
        self.imu_pub.publish(imu_msg)

    def publish_error(
        self,
        component: str,
        code: str,
        severity: str,
        message: str,
        latched: bool = False,
    ) -> None:
        """Publishes a RobotError packet adhering to contract."""
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
        if self.use_wifi and self.socket_conn:
            try:
                self.socket_conn.close()
            except Exception:
                pass
        elif not self.use_wifi and self.serial_conn and hasattr(self.serial_conn, "is_open") and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()