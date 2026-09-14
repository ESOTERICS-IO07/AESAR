"""Launch sensor interface, odometry, and localization nodes."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # 1. Sensor Interface Node
        Node(
            package="sensor_interface",
            executable="sensor_node",
            name="sensor_interface_node",
            output="screen",
            parameters=[{
                "sensor_port": "COM6",
                "baudrate": 115200,
                "read_rate_hz": 20.0,
                "mock_mode": False,
                "timeout_s": 0.1,
            }]
        ),
        # 2. Odometry Node
        Node(
            package="odometry",
            executable="odometry_node",
            name="odometry_node",
            output="screen",
            parameters=[{
                "wheel_radius_m": 0.05,
                "wheel_base_m": 0.28,
                "encoder_ticks_per_rev": 360,
                "alpha_imu": 0.95,
                "publish_rate_hz": 20.0,
            }]
        ),
        # 3. Localization Node
        Node(
            package="localization",
            executable="localization_node",
            name="localization_node",
            output="screen",
            parameters=[{
                "frame_id": "map",
                "alpha_heading": 0.95,
                "publish_rate_hz": 20.0,
            }]
        ),
    ])
