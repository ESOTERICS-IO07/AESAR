import os
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
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
        )
    ])
