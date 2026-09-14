"""Pytest configuration to automatically discover and resolve all ROS2 package sources."""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(REPO_ROOT, "ros2_ws", "src")

PACKAGES = [
    "sensor_interface",
    "odometry",
    "localization",
    "mapping",
    "exploration",
    "navigation",
    "motor_bridge",
    "arachnid_bringup",
]

for pkg in PACKAGES:
    pkg_path = os.path.join(SRC_DIR, pkg)
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)
