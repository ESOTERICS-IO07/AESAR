"""Unit & Contract Tests for navigation package."""

import numpy as np
import pytest
from mapping.grid_utils import create_grid, set_free, set_occupied
from navigation.astar import AStarPlanner
from navigation.obstacle_avoidance import ObstacleAvoidance
from navigation.velocity_controller import VelocityController


def test_astar_path_planning():
    grid = create_grid()

    # Clear open space from (-1.0, 0.0) to (1.0, 0.0)
    for y in range(80, 120):
        for x in range(80, 120):
            grid[y, x] = 0

    planner = AStarPlanner(inflation_radius_cells=2)
    start_pos = (0.0, 0.0)
    goal_pos = (0.5, 0.0)

    path = planner.plan_path(grid, start_pos, goal_pos)
    assert path is not None
    assert len(path) > 0
    assert path[0]["x_m"] == pytest.approx(0.0, abs=0.1)
    assert path[-1]["x_m"] == pytest.approx(0.5, abs=0.1)


def test_obstacle_avoidance_thresholds():
    avoidance = ObstacleAvoidance(safety_stop_distance_m=0.18, slowdown_distance_m=0.40)

    # 1. Clear distance: 1500 mm
    clear_range = {"us_fl_mm": 1500, "us_fr_mm": 1500, "tof_front_mm": 1500}
    is_blocked, speed_scale, _ = avoidance.evaluate(clear_range)
    assert not is_blocked
    assert speed_scale == 1.0

    # 2. Slowdown zone: 300 mm
    slow_range = {"us_fl_mm": 300, "us_fr_mm": 1500, "tof_front_mm": 1500}
    is_blocked, speed_scale, _ = avoidance.evaluate(slow_range)
    assert not is_blocked
    assert 0.0 < speed_scale < 1.0

    # 3. Critical stop: 100 mm (< 180 mm)
    stop_range = {"us_fl_mm": 100, "us_fr_mm": 1500, "tof_front_mm": 1500}
    is_blocked, speed_scale, _ = avoidance.evaluate(stop_range)
    assert is_blocked
    assert speed_scale == 0.0


def test_velocity_controller():
    controller = VelocityController(
        max_linear_mps=0.35,
        max_angular_rads=1.05,
        goal_tolerance_m=0.15,
    )

    path = [
        {"x_m": 0.0, "y_m": 0.0, "yaw_rad": 0.0},
        {"x_m": 0.5, "y_m": 0.0, "yaw_rad": 0.0},
        {"x_m": 1.0, "y_m": 0.0, "yaw_rad": 0.0},
    ]

    # Current robot at (0.0, 0.0, yaw=0.0)
    cmd, goal_reached = controller.compute_command(
        current_pose=(0.0, 0.0, 0.0),
        path_points=path,
        speed_scale=1.0,
        source="AUTONOMY",
    )

    assert not goal_reached
    assert cmd["source"] == "AUTONOMY"
    assert cmd["linear_mps"] > 0.0
    assert abs(cmd["angular_rads"]) < 0.2

    # Robot at goal
    cmd_at_goal, goal_reached_now = controller.compute_command(
        current_pose=(1.0, 0.0, 0.0),
        path_points=path,
        speed_scale=1.0,
        source="AUTONOMY",
    )
    assert goal_reached_now
    assert cmd_at_goal["linear_mps"] == 0.0
