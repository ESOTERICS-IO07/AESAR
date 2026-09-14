from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="motor_bridge",
            executable="motor_bridge_node",
            name="motor_bridge_node",
            output="screen",
            parameters=[{
                "drive_port": "COM5",
                "baudrate": 115200,
                "wheel_base_m": 0.28,
                "wheel_radius_m": 0.05,
                "watchdog_timeout_s": 0.50,
                "mock_mode": False,
                "timer_rate_hz": 20.0,
            }]
        )
    ])
