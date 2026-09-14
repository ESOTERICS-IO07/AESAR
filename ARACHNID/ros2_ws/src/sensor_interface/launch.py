import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    return LaunchDescription([
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
        )
    ])