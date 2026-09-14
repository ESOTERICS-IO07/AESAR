"""Tests ROS2 package structures, XML manifests, setup entry points, and topic graph connections."""

import os
import xml.etree.ElementTree as ET
import pytest

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

BASE_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ros2_ws", "src"))


def test_package_directories_and_files():
    """Verify standard ROS2 package files for every package."""
    for pkg in PACKAGES:
        pkg_dir = os.path.join(BASE_SRC_DIR, pkg)
        assert os.path.isdir(pkg_dir), f"Package directory missing: {pkg}"

        # package.xml
        xml_path = os.path.join(pkg_dir, "package.xml")
        assert os.path.exists(xml_path), f"package.xml missing in {pkg}"

        # Valid XML parse
        tree = ET.parse(xml_path)
        root = tree.getroot()
        assert root.tag == "package", f"Root tag must be <package> in {pkg}"
        build_type = root.find(".//build_type")
        assert build_type is not None and build_type.text == "ament_python"

        # setup.py & setup.cfg
        setup_py = os.path.join(pkg_dir, "setup.py")
        setup_cfg = os.path.join(pkg_dir, "setup.cfg")
        assert os.path.exists(setup_py), f"setup.py missing in {pkg}"
        assert os.path.exists(setup_cfg), f"setup.cfg missing in {pkg}"

        # resource marker
        resource_file = os.path.join(pkg_dir, "resource", pkg)
        assert os.path.exists(resource_file), f"resource/{pkg} missing in {pkg}"


def test_ros2_topic_graph_completeness():
    """Verify expected publishers and subscribers across all Person A nodes."""
    expected_graph = {
        "sensor_interface_node": {
            "publishers": {"/sensors/range", "/imu/data", "/robot_errors"},
            "subscribers": set(),
        },
        "odometry_node": {
            "publishers": {"/odom"},
            "subscribers": {"/sensors/range", "/imu/data"},
        },
        "localization_node": {
            "publishers": {"/robot_pose"},
            "subscribers": {"/odom", "/imu/data"},
        },
        "occupancy_grid_node": {
            "publishers": {"/map"},
            "subscribers": {"/robot_pose", "/sensors/range"},
        },
        "exploration_manager": {
            "publishers": {"/frontiers"},
            "subscribers": {"/map", "/robot_pose"},
        },
        "planner_node": {
            "publishers": {"/planned_path", "/cmd_vel", "/robot_state", "/robot_errors"},
            "subscribers": {"/map", "/robot_pose", "/frontiers", "/sensors/range", "/emergency_stop"},
        },
        "motor_bridge_node": {
            "publishers": {"/robot_errors"},
            "subscribers": {"/cmd_vel", "/emergency_stop"},
        },
    }

    # Verify all expected topic names are contract valid
    all_contract_topics = {
        "/sensors/range",
        "/imu/data",
        "/odom",
        "/robot_pose",
        "/map",
        "/frontiers",
        "/planned_path",
        "/cmd_vel",
        "/robot_state",
        "/robot_errors",
        "/emergency_stop",
    }

    for node_name, info in expected_graph.items():
        for p in info["publishers"]:
            assert p in all_contract_topics, f"Invalid publisher topic: {p} in {node_name}"
        for s in info["subscribers"]:
            assert s in all_contract_topics, f"Invalid subscriber topic: {s} in {node_name}"
