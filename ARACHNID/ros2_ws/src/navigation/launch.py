from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="navigation",
            executable="planner_node",
            name="planner_node",
            output="screen",
            parameters=[{
                "max_linear_speed_mps": 0.35,
                "max_angular_speed_rads": 1.05,
                "safety_stop_distance_m": 0.18,
                "slowdown_distance_m": 0.40,
                "goal_tolerance_m": 0.15,
                "obstacle_inflation_cells": 3,
                "control_rate_hz": 20.0,
            }]
        )
    ])
