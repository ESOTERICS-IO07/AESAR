"""Launch path planner and motor bridge nodes."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # Path Planner Node
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
        ),
        # Motor Bridge Node
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
        ),
    ])
