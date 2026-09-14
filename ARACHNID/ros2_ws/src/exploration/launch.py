from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="exploration",
            executable="exploration_manager",
            name="exploration_manager",
            output="screen",
            parameters=[{
                "min_cluster_size": 2,
                "max_frontiers_to_publish": 10,
                "publish_rate_hz": 2.0,
            }]
        )
    ])
