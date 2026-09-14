import pytest
from backend.models.schemas import SensorStatus
from backend.hardware.adapters import (
    ExplorationAdapter,
    MapAdapter,
    NavigationAdapter,
    SensorAdapter,
)


def test_sensor_adapter_valid_readings():
    raw = {
        "timestamp_ms": 1000,
        "us_fl_mm": 1200.0,
        "us_fr_mm": 950.0,
        "us_l_mm": 760.0,
        "us_r_mm": 1430.0,
        "tof_front_mm": 880.0,
    }
    telemetry = SensorAdapter.convert_raw_telemetry(raw, seq=1)

    assert telemetry.seq == 1
    assert telemetry.us_fl_mm == 1200.0
    assert telemetry.sensor_status.us_fl == SensorStatus.OK
    assert telemetry.sensor_status.tof_front == SensorStatus.OK


def test_sensor_adapter_out_of_range():
    raw = {
        "us_fl_mm": 5500.0,  # exceeds 4000mm limit
        "us_fr_mm": 5.0,     # below 20mm limit
        "tof_front_mm": 2500.0, # exceeds 2000mm ToF limit
    }
    telemetry = SensorAdapter.convert_raw_telemetry(raw, seq=2)

    assert telemetry.sensor_status.us_fl == SensorStatus.OUT_OF_RANGE
    assert telemetry.sensor_status.us_fr == SensorStatus.OUT_OF_RANGE
    assert telemetry.sensor_status.tof_front == SensorStatus.OUT_OF_RANGE


def test_sensor_adapter_disconnected():
    raw = {
        "us_fl_mm": -1.0,
        "us_fr_mm": None,
    }
    telemetry = SensorAdapter.convert_raw_telemetry(raw, seq=3)

    assert telemetry.sensor_status.us_fl == SensorStatus.DISCONNECTED
    assert telemetry.sensor_status.us_fr == SensorStatus.DISCONNECTED


def test_map_adapter():
    raw_map = {
        "info": {
            "resolution": 0.05,
            "width": 10,
            "height": 10,
            "origin": {"position": {"x": 1.0, "y": 2.0}},
        },
        "data": [0] * 100,
    }
    map_data = MapAdapter.convert_occupancy_grid(raw_map)

    assert map_data.resolution_m_per_cell == 0.05
    assert map_data.width == 10
    assert map_data.height == 10
    assert map_data.origin.x == 1.0
    assert map_data.origin.y == 2.0
    assert len(map_data.data) == 100


def test_navigation_adapter():
    raw_nav = {
        "status": "NAVIGATING",
        "goal": {"x": 4.5, "y": 2.0},
        "path": [{"x": 0.0, "y": 0.0}, {"x": 2.0, "y": 1.0}, {"x": 4.5, "y": 2.0}],
    }
    nav_data = NavigationAdapter.convert_navigation_data(raw_nav)

    assert nav_data.status == "NAVIGATING"
    assert nav_data.goal is not None
    assert nav_data.goal.x == 4.5
    assert len(nav_data.path) == 3


def test_exploration_adapter():
    raw_exp = {
        "status": "EXPLORING",
        "explored_percent": 35.5,
        "frontier_count": 4,
        "current_goal": {"x": 2.0, "y": 3.0},
    }
    exp_data = ExplorationAdapter.convert_exploration_data(raw_exp)

    assert exp_data.status == "EXPLORING"
    assert exp_data.explored_percent == 35.5
    assert exp_data.frontier_count == 4
    assert exp_data.current_goal is not None
    assert exp_data.current_goal.x == 2.0
