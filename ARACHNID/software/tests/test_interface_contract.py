#!/usr/bin/env python3

"""
ARACHNID B1 Contract Verification Suite

Validates the frozen B1 configuration contract:

1. All required YAML files exist and parse.
2. Frozen interface names, states, modes, sources and units.
3. Hardware sensor configuration.
4. Robot/network configuration.
5. Command configuration.
6. REST API contract.
7. WebSocket contract.

This test file intentionally does NOT prohibit B2 implementation code.
B1 configuration contracts remain frozen while backend implementation proceeds.
"""

from pathlib import Path

import pytest
import yaml


CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


REQUIRED_CONFIG_FILES = [
    "interfaces.yaml",
    "hardware.yaml",
    "robot.yaml",
    "commands.yaml",
    "api.yaml",
    "websocket.yaml",
]


FROZEN_SENSOR_STATUSES = [
    "OK",
    "TIMEOUT",
    "OUT_OF_RANGE",
    "DISCONNECTED",
    "INVALID",
]

FROZEN_ROVER_MODES = [
    "MANUAL",
    "AUTONOMOUS",
]

FROZEN_COMMAND_SOURCES = [
    "MANUAL",
    "AUTONOMY",
    "SYSTEM",
]

FROZEN_ROVER_STATES = [
    "DISCONNECTED",
    "CONNECTING",
    "IDLE",
    "MANUAL",
    "AUTONOMOUS",
    "NAVIGATING",
    "EXPLORING",
    "EMERGENCY_STOP",
    "FAULT",
]

FROZEN_SENSOR_NAMES = [
    "us_fl",
    "us_fr",
    "us_l",
    "us_r",
    "tof_front",
]

FROZEN_TELEMETRY_FIELDS = [
    "us_fl_mm",
    "us_fr_mm",
    "us_l_mm",
    "us_r_mm",
    "tof_front_mm",
]

FROZEN_WEBSOCKET_EVENTS = [
    "rover_status",
    "sensor_telemetry",
    "map_update",
    "navigation_update",
    "exploration_update",
    "battery_update",
    "log_event",
    "safety_event",
]

FROZEN_API_ENDPOINTS = [
    ("GET", "/api/health"),
    ("GET", "/api/rover/status"),
    ("GET", "/api/rover/telemetry"),
    ("POST", "/api/rover/mode"),
    ("POST", "/api/rover/command"),
    ("POST", "/api/rover/stop"),
    ("POST", "/api/rover/emergency-stop"),
    ("POST", "/api/rover/emergency-stop/reset"),
    ("GET", "/api/map"),
    ("GET", "/api/navigation"),
    ("GET", "/api/exploration"),
    ("GET", "/api/logs"),
]


def load_yaml(filename: str) -> dict:
    filepath = CONFIG_DIR / filename

    assert filepath.exists(), (
        f"Missing required config file: {filename}"
    )

    with open(filepath, "r", encoding="utf-8") as file:
        content = yaml.safe_load(file)

    assert content is not None, (
        f"YAML file {filename} is empty"
    )

    assert isinstance(content, dict), (
        f"YAML file {filename} must contain a mapping/object"
    )

    return content


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def interfaces():
    return load_yaml("interfaces.yaml")


@pytest.fixture
def hardware():
    return load_yaml("hardware.yaml")


@pytest.fixture
def robot_cfg():
    return load_yaml("robot.yaml")


@pytest.fixture
def commands():
    return load_yaml("commands.yaml")


@pytest.fixture
def api_cfg():
    return load_yaml("api.yaml")


@pytest.fixture
def ws_cfg():
    return load_yaml("websocket.yaml")


# ---------------------------------------------------------------------------
# YAML existence / parsing
# ---------------------------------------------------------------------------

def test_yaml_files_exist_and_parse():
    for filename in REQUIRED_CONFIG_FILES:
        load_yaml(filename)


# ---------------------------------------------------------------------------
# interfaces.yaml
# ---------------------------------------------------------------------------

def test_interfaces_definitions(interfaces):
    assert interfaces.get("version") == "1.0.0"

    sensor_statuses = (
        interfaces.get("sensor_status", {})
        .get("values", [])
    )

    assert sensor_statuses == FROZEN_SENSOR_STATUSES

    rover_modes = (
        interfaces.get("rover_modes", {})
        .get("values", [])
    )

    assert rover_modes == FROZEN_ROVER_MODES

    command_sources = (
        interfaces.get("command_sources", {})
        .get("values", [])
    )

    assert command_sources == FROZEN_COMMAND_SOURCES

    rover_states = (
        interfaces.get("rover_states", {})
        .get("values", [])
    )

    assert rover_states == FROZEN_ROVER_STATES

    telemetry = interfaces.get("telemetry", {})

    ultrasonic = telemetry.get("ultrasonic", {})

    assert ultrasonic.get("fields") == [
        "us_fc_mm",
        "us_fl_mm",
        "us_fr_mm",
        "us_l_mm",
        "us_r_mm",
    ]

    assert ultrasonic.get("unit") == "mm"
    assert ultrasonic.get("invalid_value") == -1

    tof = telemetry.get("tof", {})

    assert tof.get("field") == "tof_front_mm"
    assert tof.get("unit") == "mm"
    assert tof.get("invalid_value") == -1

    imu = telemetry.get("imu", {})

    assert imu.get("acceleration_unit") == "m/s2"
    assert imu.get("angular_velocity_unit") == "rad/s"

    encoders = telemetry.get("encoders", {})

    assert encoders.get("unit") == "ticks"

    battery = telemetry.get("battery", {})

    assert battery.get("field") == "battery_percent"
    assert battery.get("unit") == "percent"
    assert battery.get("invalid_value") == -1


# ---------------------------------------------------------------------------
# hardware.yaml
# ---------------------------------------------------------------------------

def test_hardware_definitions(hardware):
    sensors = hardware.get("sensors", {})

    ultrasonic = sensors.get("ultrasonic", {})

    assert ultrasonic.get("count") == 5

    assert ultrasonic.get("names") == [
        "us_fc",
        "us_fl",
        "us_fr",
        "us_l",
        "us_r",
    ]

    assert ultrasonic.get("max_range_mm") == "TBD"
    assert ultrasonic.get("update_hz") == "TBD"

    tof = sensors.get("tof_front", {})

    assert tof.get("enabled") is True
    assert tof.get("model") == "TBD"
    assert tof.get("max_range_mm") == "TBD"
    assert tof.get("update_hz") == "TBD"

    imu = sensors.get("imu", {})

    assert imu.get("enabled") is False
    assert imu.get("model") == "TBD"
    assert imu.get("update_hz") == "TBD"

    encoders = sensors.get("encoders", {})

    assert encoders.get("enabled") is False
    assert encoders.get("ticks_per_rev") == "TBD"

    robot = hardware.get("robot", {})

    assert robot.get("wheel_diameter_m") == "TBD"
    assert robot.get("track_width_m") == "TBD"
    assert robot.get("footprint_length_m") == "TBD"
    assert robot.get("footprint_width_m") == "TBD"

    power = hardware.get("power", {})

    assert power.get("battery_nominal_v") == "TBD"
    assert power.get("logic_voltage_v") == "TBD"

    safety = hardware.get("safety", {})

    assert safety.get("command_timeout_ms") == "TBD"
    assert safety.get("max_linear_mps") == "TBD"
    assert safety.get("max_angular_rads") == "TBD"
    assert safety.get("minimum_obstacle_distance_mm") == "TBD"


# ---------------------------------------------------------------------------
# robot.yaml
# ---------------------------------------------------------------------------

def test_robot_definitions(robot_cfg):
    robot = robot_cfg.get("robot", {})

    assert robot.get("name") == "ARACHNID"
    assert robot.get("default_mode") == "MANUAL"
    assert robot.get("initial_state") == "DISCONNECTED"

    coordinate_frames = robot.get("coordinate_frames", {})

    assert coordinate_frames.get("base") == "base_link"
    assert coordinate_frames.get("odometry") == "odom"
    assert coordinate_frames.get("map") == "map"

    backend = robot_cfg.get("backend", {})

    assert backend.get("host") == "0.0.0.0"
    assert backend.get("port") == 8000

    frontend = robot_cfg.get("frontend", {})

    assert frontend.get("websocket_path") == "/ws"

    logging_cfg = robot_cfg.get("logging", {})

    assert logging_cfg.get("level") == "INFO"


# ---------------------------------------------------------------------------
# commands.yaml
# ---------------------------------------------------------------------------

def test_commands_definitions(commands):
    velocity_command = commands.get(
        "velocity_command",
        {},
    )

    fields = velocity_command.get(
        "fields",
        {},
    )

    assert "command_id" in fields
    assert "timestamp_ms" in fields
    assert "linear_mps" in fields

    assert fields["linear_mps"].get("unit") == "m/s"

    assert "angular_rads" in fields

    assert fields["angular_rads"].get("unit") == "rad/s"

    assert "source" in fields

    assert fields["source"].get(
        "allowed_values"
    ) == FROZEN_COMMAND_SOURCES

    example = velocity_command.get(
        "example",
        {},
    )

    assert example.get(
        "source"
    ) in FROZEN_COMMAND_SOURCES

    safety = commands.get(
        "safety_limits",
        {},
    )

    assert safety.get("command_timeout_ms") == "TBD"
    assert safety.get("max_linear_mps") == "TBD"
    assert safety.get("max_angular_rads") == "TBD"


# ---------------------------------------------------------------------------
# api.yaml
# ---------------------------------------------------------------------------

def test_api_definitions(api_cfg):
    endpoints = api_cfg.get(
        "endpoints",
        {},
    )

    seen_endpoints = set()

    for name, endpoint in endpoints.items():
        method = endpoint.get("method")
        path = endpoint.get("path")

        endpoint_tuple = (
            method,
            path,
        )

        assert endpoint_tuple not in seen_endpoints, (
            f"Duplicate endpoint: {endpoint_tuple}"
        )

        seen_endpoints.add(endpoint_tuple)

    for expected_method, expected_path in FROZEN_API_ENDPOINTS:
        assert (
            expected_method,
            expected_path,
        ) in seen_endpoints, (
            f"Missing required endpoint: "
            f"{expected_method} {expected_path}"
        )

    rover_status_resp = endpoints[
        "rover_status"
    ]["response"]

    assert rover_status_resp["state"] in FROZEN_ROVER_STATES
    assert rover_status_resp["mode"] in FROZEN_ROVER_MODES

    telemetry_resp = endpoints[
        "rover_telemetry"
    ]["response"]

    for field in FROZEN_TELEMETRY_FIELDS:
        assert field in telemetry_resp

    sensor_status = telemetry_resp[
        "sensor_status"
    ]

    for sensor_name in FROZEN_SENSOR_NAMES:
        assert sensor_name in sensor_status
        assert (
            sensor_status[sensor_name]
            in FROZEN_SENSOR_STATUSES
        )

    command_request = endpoints[
        "rover_command"
    ]["request"]

    assert "command_id" in command_request
    assert "timestamp_ms" in command_request
    assert "linear_mps" in command_request
    assert "angular_rads" in command_request

    assert command_request["source"] in (
        FROZEN_COMMAND_SOURCES
    )

    map_response = endpoints[
        "map"
    ]["response"]

    for key in [
        "resolution_m_per_cell",
        "width",
        "height",
        "origin",
        "data",
    ]:
        assert key in map_response

    navigation_response = endpoints[
        "navigation"
    ]["response"]

    for key in [
        "status",
        "goal",
        "path",
    ]:
        assert key in navigation_response

    exploration_response = endpoints[
        "exploration"
    ]["response"]

    for key in [
        "status",
        "explored_percent",
        "frontier_count",
        "current_goal",
    ]:
        assert key in exploration_response


# ---------------------------------------------------------------------------
# websocket.yaml
# ---------------------------------------------------------------------------

def test_websocket_definitions(ws_cfg):
    websocket = ws_cfg.get(
        "websocket",
        {},
    )

    assert websocket.get("path") == "/ws"

    event_types = websocket.get(
        "event_types",
        [],
    )

    assert len(event_types) == len(
        set(event_types)
    )

    assert event_types == FROZEN_WEBSOCKET_EVENTS

    events = websocket.get(
        "events",
        {},
    )

    for event_type in FROZEN_WEBSOCKET_EVENTS:
        assert event_type in events

        schema = events[
            event_type
        ].get(
            "schema",
            {},
        )

        assert schema.get("type") == event_type
        assert "timestamp_ms" in schema
        assert "data" in schema

    telemetry_data = events[
        "sensor_telemetry"
    ]["schema"]["data"]

    for field in FROZEN_TELEMETRY_FIELDS:
        assert field in telemetry_data

    rover_status_data = events[
        "rover_status"
    ]["schema"]["data"]

    assert (
        rover_status_data["state"]
        in FROZEN_ROVER_STATES
    )

    assert (
        rover_status_data["mode"]
        in FROZEN_ROVER_MODES
    )
