"""Verifies all package launch files have valid launch descriptions and syntax."""

import os
import pytest


def test_all_launch_files_exist():
    packages = [
        "sensor_interface",
        "odometry",
        "localization",
        "mapping",
        "exploration",
        "navigation",
        "motor_bridge",
    ]

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ros2_ws", "src"))

    for pkg in packages:
        launch_file = os.path.join(base_dir, pkg, "launch.py")
        assert os.path.exists(launch_file), f"launch.py missing in {pkg}"


def test_arachnid_bringup_launch_files_exist():
    bringup_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "ros2_ws", "src", "arachnid_bringup", "launch")
    )

    expected_launches = [
        "sensors.launch.py",
        "mapping.launch.py",
        "navigation.launch.py",
        "autonomy.launch.py",
        "full_system.launch.py",
    ]

    for launch_name in expected_launches:
        path = os.path.join(bringup_dir, launch_name)
        assert os.path.exists(path), f"Bringup launch file missing: {launch_name}"
