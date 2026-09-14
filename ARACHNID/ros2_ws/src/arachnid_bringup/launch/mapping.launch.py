"""Launch sensors and occupancy grid mapping nodes."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Sensor Interface
        Node(
            package="sensor_interface",
            executable="sensor_node",
            name="sensor_interface_node",
            output="screen",
        ),
        # Odometry
        Node(
            package="odometry",
            executable="odometry_node",
            name="odometry_node",
            output="screen",
        ),
        # Localization
        Node(
            package="localization",
            executable="localization_node",
            name="localization_node",
            output="screen",
        ),
        # Occupancy Grid Mapping
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
        ),
    ])
