"""Unified single-command full autonomous rover system launcher."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # 1. Sensor Interface
        Node(
            package="sensor_interface",
            executable="sensor_node",
            name="sensor_interface_node",
            output="screen",
        ),
        # 2. Odometry
        Node(
            package="odometry",
            executable="odometry_node",
            name="odometry_node",
            output="screen",
        ),
        # 3. Localization
        Node(
            package="localization",
            executable="localization_node",
            name="localization_node",
            output="screen",
        ),
        # 4. Mapping
        Node(
            package="mapping",
            executable="occupancy_grid_node",
            name="occupancy_grid_node",
            output="screen",
        ),
        # 5. Exploration
        Node(
            package="exploration",
            executable="exploration_manager",
            name="exploration_manager",
            output="screen",
        ),
        # 6. Navigation Planner
        Node(
            package="navigation",
            executable="planner_node",
            name="planner_node",
            output="screen",
        ),
        # 7. Motor Bridge
        Node(
            package="motor_bridge",
            executable="motor_bridge_node",
            name="motor_bridge_node",
            output="screen",
        ),
    ])
