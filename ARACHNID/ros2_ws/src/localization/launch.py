from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
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
        )
    ])
