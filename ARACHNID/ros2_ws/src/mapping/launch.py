from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="mapping",
            executable="occupancy_grid_node",
            name="occupancy_grid_node",
            output="screen",
            parameters=[{
                "min_range_m": 0.02,
                "max_range_m": 2.50,
                "publish_rate_hz": 5.0,
            }]
        )
    ])
