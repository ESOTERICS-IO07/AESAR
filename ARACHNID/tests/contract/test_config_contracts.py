"""Validates all YAML configuration files in config/ against Contract v1.0.0."""

import os
import pytest
import yaml

CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config"))


def load_yaml(filename: str):
    path = os.path.join(CONFIG_DIR, filename)
    assert os.path.exists(path), f"Configuration file {filename} not found in {CONFIG_DIR}"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_robot_config_yaml():
    cfg = load_yaml("robot_config.yaml")
    assert "robot" in cfg
    assert "serial" in cfg
    assert cfg["robot"]["wheel_radius_m"] == 0.05
    assert cfg["robot"]["wheel_base_m"] == 0.28
    assert cfg["robot"]["encoder_ticks_per_rev"] == 360
    assert cfg["serial"]["baudrate"] == 115200


def test_sensor_config_yaml():
    cfg = load_yaml("sensor_config.yaml")
    assert "sensors" in cfg
    sensors = cfg["sensors"]
    assert "ultrasonic" in sensors
    assert "tof" in sensors
    assert "imu" in sensors

    us = sensors["ultrasonic"]
    assert "us_fl" in us
    assert "us_fr" in us
    assert "us_l" in us
    assert "us_r" in us


def test_navigation_config_yaml():
    cfg = load_yaml("navigation_config.yaml")
    assert "navigation" in cfg
    assert "safety" in cfg
    assert "planner" in cfg

    assert cfg["navigation"]["max_linear_speed_mps"] == 0.35
    assert cfg["navigation"]["max_angular_speed_rads"] == 1.05
    assert cfg["safety"]["safety_stop_distance_m"] == 0.18
    assert cfg["safety"]["slowdown_distance_m"] == 0.40
    assert cfg["safety"]["watchdog_timeout_s"] == 0.50


def test_mapping_config_yaml():
    cfg = load_yaml("mapping_config.yaml")
    assert "mapping" in cfg
    assert "grid_values" in cfg

    m = cfg["mapping"]
    assert m["frame_id"] == "map"
    assert m["resolution_m_per_cell"] == 0.05
    assert m["width"] == 200
    assert m["height"] == 200
    assert m["origin_x_m"] == -5.0
    assert m["origin_y_m"] == -5.0

    gv = cfg["grid_values"]
    assert gv["unknown"] == -1
    assert gv["free"] == 0
    assert gv["occupied"] == 100


def test_exploration_config_yaml():
    cfg = load_yaml("exploration_config.yaml")
    assert "exploration" in cfg
    assert "scoring" in cfg
    assert cfg["exploration"]["min_cluster_size"] == 2
    assert cfg["exploration"]["max_frontiers_to_publish"] == 10
