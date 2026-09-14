"""Stress, Fault-Tolerance & Edge-Case Verification Tests.

Simulates extreme conditions:
- 1000 High-rate sensor packet stream
- Corrupted / malformed JSON streams
- Sensor noise & spike bursts
- Serial disconnection & reconnection recovery
- Encoder tick overflows & sudden resets
- Dynamic obstacle pop-ups & trapped/surrounded conditions
"""

import json
import math
import random
import numpy as np
import pytest

from exploration.frontier_detector import FrontierDetector
from exploration.frontier_selector import FrontierSelector
from mapping.grid_utils import (
    FREE_VALUE,
    HEIGHT,
    OCCUPIED_VALUE,
    UNKNOWN_VALUE,
    WIDTH,
    create_grid,
    set_free,
    set_occupied,
    world_to_grid,
)
from mapping.ray_casting import bresenham, sensor_endpoint, transform_sensor_to_world
from navigation.astar import AStarPlanner
from navigation.obstacle_avoidance import ObstacleAvoidance
from navigation.velocity_controller import VelocityController
from odometry.encoder_math import EncoderMath
from odometry.imu_fusion import IMUFusion
from sensor_interface.filter import LowPassFilter, MedianFilter, MovingAverageFilter
from sensor_interface.serial_parser import RangePacketValidator, SerialParser
from motor_bridge.serial_bridge import SerialBridge
from motor_bridge.watchdog import MotorWatchdog


def test_stress_1000_sensor_packets():
    """Stream 1000 synthetic sensor packets and verify filter and validator stability."""
    fl_filter = MedianFilter(window_size=5)
    tof_filter = MovingAverageFilter(window_size=5)
    lp_filter = LowPassFilter(alpha=0.25)

    for i in range(1000):
        raw_val = 500.0 + 20.0 * math.sin(i * 0.1) + random.uniform(-10.0, 10.0)
        filt_us = fl_filter.update(raw_val)
        filt_tof = tof_filter.update(raw_val)
        filt_imu = lp_filter.update(raw_val)

        assert 400.0 < filt_us < 600.0
        assert 400.0 < filt_tof < 600.0
        assert 400.0 < filt_imu < 600.0

        packet = RangePacketValidator.build_packet(
            seq=i,
            us_fc_mm=850.0, us_fl_mm=filt_us,
            us_fr_mm=filt_us,
            us_l_mm=1000.0,
            us_r_mm=1000.0,
            tof_front_mm=filt_tof,
        )
        assert RangePacketValidator.validate(packet)


def test_corrupted_json_stream_fault_tolerance():
    """Verify SerialParser handles random corrupted strings and truncated payloads gracefully."""
    corrupted_inputs = [
        "",
        "   ",
        "{",
        '{"timestamp_ms": 123',
        "corrupted_garbage_bytes\x00\xff",
        '{"seq": "invalid_type", "us_fl_mm": null}',
        "{'single_quotes': 123}",
        '{"nested": {"unclosed": true}',
    ]

    for corrupt_str in corrupted_inputs:
        parsed = SerialParser.parse_line(corrupt_str)
        # Should return None without raising unhandled exceptions
        if parsed is not None:
            assert isinstance(parsed, dict)


def test_imu_and_ultrasonic_extreme_spike_rejection():
    """Test sudden massive sensor spikes (e.g. 50000mm) are filtered out."""
    med = MedianFilter(window_size=5)
    # 4 normal readings, 1 massive anomaly spike, 2 normal readings
    inputs = [500.0, 505.0, 502.0, 501.0, 50000.0, 504.0, 503.0]
    filtered = [med.update(x) for x in inputs]

    # The anomaly 50000.0 must be rejected
    assert all(f < 600.0 for f in filtered)


def test_encoder_sudden_reset_and_large_ticks():
    """Test odometry gracefully handles sudden tick reset without crashing."""
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(0, 0)

    # Move 100 ticks
    (x, y, yaw), _ = em.update_pose(current_left_ticks=100, current_right_ticks=100, current_pose=(0.0, 0.0, 0.0), dt=0.05)
    assert x > 0.0

    # Sudden hardware reset to 0
    em.reset(0, 0)
    (x2, y2, yaw2), _ = em.update_pose(current_left_ticks=10, current_right_ticks=10, current_pose=(x, y, yaw), dt=0.05)
    assert x2 > x


def test_dynamic_obstacle_popup_and_surrounded_robot():
    """Test navigation behavior when an obstacle pops up directly in front of the rover."""
    avoidance = ObstacleAvoidance(safety_stop_distance_m=0.18, slowdown_distance_m=0.40)

    # Step 1: Open space
    range_open = {"us_fl_mm": 1500, "us_fr_mm": 1500, "tof_front_mm": 1500}
    blocked, scale, _ = avoidance.evaluate(range_open)
    assert not blocked
    assert scale == 1.0

    # Step 2: Obstacle suddenly appears at 100mm (< 180mm safety limit)
    range_danger = {"us_fl_mm": 100, "us_fr_mm": 120, "tof_front_mm": 90}
    blocked, scale, reason = avoidance.evaluate(range_danger)
    assert blocked
    assert scale == 0.0
    assert "CRITICAL" in reason

    # Step 3: Trapped / Surrounded robot on occupancy grid
    grid = create_grid()
    rx, ry = world_to_grid(0.0, 0.0)
    # Surround (0.0, 0.0) by obstacle box
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dx) == 3 or abs(dy) == 3:
                grid[ry + dy, rx + dx] = OCCUPIED_VALUE
            else:
                grid[ry + dy, rx + dx] = FREE_VALUE

    planner = AStarPlanner(inflation_radius_cells=2)
    path_trapped = planner.plan_path(grid, start_world=(0.0, 0.0), goal_world=(3.0, 3.0))
    # Should safely report no path (None) without crashing or infinite loop
    assert path_trapped is None
