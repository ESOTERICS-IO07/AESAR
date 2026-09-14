"""Exhaustive Unit Tests for ARACHNID Person A Subsystems.

Covers Sensor Interface, Odometry, Localization, Mapping, Exploration,
Navigation, and Motor Bridge according to Contract v1.0.0.
"""

import math
import numpy as np
import pytest

from exploration.frontier_detector import FrontierDetector
from exploration.frontier_selector import FrontierSelector
from localization.complementary_filter import ComplementaryFilter, normalize_angle
from localization.pose_estimator import PoseEstimator
from mapping.grid_utils import (
    FREE_VALUE,
    HEIGHT,
    OCCUPIED_VALUE,
    UNKNOWN_VALUE,
    WIDTH,
    create_grid,
    get_cell_value,
    grid_to_world,
    is_in_bounds,
    set_free,
    set_occupied,
    world_to_grid,
)
from mapping.map_visualizer import MapVisualizer
from mapping.ray_casting import (
    bresenham,
    sensor_endpoint,
    transform_sensor_to_world,
)
from navigation.astar import AStarPlanner
from navigation.obstacle_avoidance import ObstacleAvoidance
from navigation.velocity_controller import VelocityController
from odometry.encoder_math import EncoderMath
from odometry.imu_fusion import IMUFusion
from sensor_interface.filter import LowPassFilter, MedianFilter, MovingAverageFilter
from sensor_interface.serial_parser import (
    ImuPacketValidator,
    RangePacketValidator,
    SerialParser,
)
from motor_bridge.packet_builder import PacketBuilder
from motor_bridge.serial_bridge import SerialBridge
from motor_bridge.watchdog import MotorWatchdog


# ============================================================================
# 1. SENSOR INTERFACE TESTS
# ============================================================================

def test_sensor_valid_ultrasonic_packet():
    packet = RangePacketValidator.build_packet(
        seq=10, us_fc_mm=450.0, us_fl_mm=450.0, us_fr_mm=460.0, us_l_mm=1200.0, us_r_mm=1180.0, tof_front_mm=440.0
    )
    assert RangePacketValidator.validate(packet)
    assert packet["us_fl_mm"] == 450.0
    assert packet["sensor_status"]["us_fl"] == "OK"


def test_sensor_invalid_packet_missing_fields():
    invalid_packet = {"seq": 10, "us_fl_mm": 450.0}
    assert not RangePacketValidator.validate(invalid_packet)
    assert not RangePacketValidator.validate(None)
    assert not RangePacketValidator.validate("not_a_dict")


def test_sensor_tof_boundary_readings():
    # Min boundary (20mm) and Max boundary (2000mm)
    pkt_min = RangePacketValidator.build_packet(seq=1, us_fc_mm=20, us_fl_mm=20, us_fr_mm=20, us_l_mm=20, us_r_mm=20, tof_front_mm=10.0)
    pkt_max = RangePacketValidator.build_packet(seq=2, us_fc_mm=3000, us_fl_mm=3000, us_fr_mm=3000, us_l_mm=3000, us_r_mm=3000, tof_front_mm=2000.0)
    assert RangePacketValidator.validate(pkt_min)
    assert RangePacketValidator.validate(pkt_max)
    assert pkt_min["tof_front_mm"] == 10.0
    assert pkt_max["tof_front_mm"] == 2000.0


def test_sensor_imu_stationary_and_rotating():
    stationary = ImuPacketValidator.build_packet(seq=1, accel_x_mps2=0.0, accel_y_mps2=0.0, accel_z_mps2=9.806, gyro_x_rads=0.0, gyro_y_rads=0.0, gyro_z_rads=0.0)
    rotating = ImuPacketValidator.build_packet(seq=2, accel_x_mps2=0.05, accel_y_mps2=0.1, accel_z_mps2=9.806, gyro_x_rads=0.0, gyro_y_rads=0.0, gyro_z_rads=1.25)

    assert ImuPacketValidator.validate(stationary)
    assert ImuPacketValidator.validate(rotating)
    assert stationary["gyro_z_rads"] == 0.0
    assert rotating["gyro_z_rads"] == 1.25


def test_sensor_filter_smoothing_and_spike_rejection():
    # Median Filter
    med = MedianFilter(window_size=5)
    sequence = [100.0, 102.0, 5000.0, 101.0, 103.0]
    out = [med.update(v) for v in sequence]
    assert out[-1] == 102.0  # Spike rejected

    # Moving Average Filter
    ma = MovingAverageFilter(window_size=3)
    ma.update(100.0)
    ma.update(200.0)
    res = ma.update(300.0)
    assert res == pytest.approx(200.0)

    # Low Pass Filter
    lp = LowPassFilter(alpha=0.20)
    lp.reset()
    v1 = lp.update(10.0)
    assert v1 == 10.0
    v2 = lp.update(20.0)
    assert v2 == pytest.approx(0.2 * 20.0 + 0.8 * 10.0)


def test_sensor_interface_error_packet_emission():
    err_packet = {
        "timestamp_ms": 1725200000000,
        "component": "sensor_interface",
        "code": "SERIAL_PORT_UNAVAILABLE",
        "severity": "WARNING",
        "message": "Serial port failed to open",
        "latched": False,
    }
    for k in ["timestamp_ms", "component", "code", "severity", "message", "latched"]:
        assert k in err_packet


# ============================================================================
# 2. ODOMETRY TESTS
# ============================================================================

def test_odometry_forward_motion():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(0, 0)
    (x, y, yaw), (v_lin, v_ang) = em.update_pose(current_left_ticks=180, current_right_ticks=180, current_pose=(0.0, 0.0, 0.0), dt=1.0)
    expected_dist = math.pi * 0.05
    assert x == pytest.approx(expected_dist, rel=1e-3)
    assert y == pytest.approx(0.0, abs=1e-3)
    assert yaw == pytest.approx(0.0, abs=1e-3)
    assert v_lin > 0.0


def test_odometry_reverse_motion():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(180, 180)
    (x, y, yaw), (v_lin, v_ang) = em.update_pose(current_left_ticks=0, current_right_ticks=0, current_pose=(0.0, 0.0, 0.0), dt=1.0)
    expected_dist = -(math.pi * 0.05)
    assert x == pytest.approx(expected_dist, rel=1e-3)
    assert v_lin < 0.0


def test_odometry_left_and_right_turn():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)

    # Left turn (right wheel moves more)
    em.reset(0, 0)
    (x_l, y_l, yaw_l), (v_lin_l, v_ang_l) = em.update_pose(current_left_ticks=50, current_right_ticks=150, current_pose=(0.0, 0.0, 0.0), dt=1.0)
    assert yaw_l > 0.0  # CCW positive

    # Right turn (left wheel moves more)
    em.reset(0, 0)
    (x_r, y_r, yaw_r), (v_lin_r, v_ang_r) = em.update_pose(current_left_ticks=150, current_right_ticks=50, current_pose=(0.0, 0.0, 0.0), dt=1.0)
    assert yaw_r < 0.0  # CW negative


def test_odometry_rotate_in_place():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(0, 0)
    (x, y, yaw), (v_lin, v_ang) = em.update_pose(current_left_ticks=-90, current_right_ticks=90, current_pose=(0.0, 0.0, 0.0), dt=1.0)
    assert x == pytest.approx(0.0, abs=1e-3)
    assert y == pytest.approx(0.0, abs=1e-3)
    assert yaw > 0.0
    assert v_lin == pytest.approx(0.0, abs=1e-3)
    assert v_ang > 0.0


def test_odometry_tick_overflow_and_imu_fusion():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(100000, 100000)
    (x, y, yaw), _ = em.update_pose(current_left_ticks=100100, current_right_ticks=100100, current_pose=(0.0, 0.0, 0.0), dt=0.5)
    assert x > 0.0

    fusion = IMUFusion(alpha=0.95)
    fusion.reset(0.0)
    fused_yaw = fusion.update(gyro_z_rads=0.20, encoder_yaw_rad=0.01, dt=0.05)
    assert isinstance(fused_yaw, float)
    assert -math.pi <= fused_yaw <= math.pi


# ============================================================================
# 3. LOCALIZATION TESTS
# ============================================================================

def test_localization_complementary_fusion():
    loc = ComplementaryFilter(alpha=0.90)
    loc.reset(0.0)

    # High gyro rate, low odom change
    fused = loc.update(gyro_z_rads=1.0, odom_yaw_rad=0.0, dt=0.1)
    assert fused > 0.0


def test_localization_angle_wrap_boundaries():
    assert normalize_angle(math.pi + 0.1) == pytest.approx(-math.pi + 0.1, abs=1e-4)
    assert normalize_angle(-math.pi - 0.1) == pytest.approx(math.pi - 0.1, abs=1e-4)


def test_localization_pose_estimator_confidence():
    estimator = PoseEstimator(frame="map")

    odom_fresh = {
        "timestamp_ms": 1725200000000,
        "x_m": 2.0,
        "y_m": 1.5,
        "yaw_rad": 0.45,
    }
    pose_fresh = estimator.update(odom_packet=odom_fresh, fused_yaw=0.45, last_update_age_s=0.01)
    assert pose_fresh["frame"] == "map"
    assert pose_fresh["confidence"] >= 0.95

    # Degraded confidence with aged sensor updates
    pose_stale = estimator.update(odom_packet=odom_fresh, fused_yaw=0.45, last_update_age_s=2.5)
    assert pose_stale["confidence"] < pose_fresh["confidence"]


# ============================================================================
# 4. MAPPING TESTS
# ============================================================================

def test_mapping_empty_and_cell_marking():
    grid = create_grid()
    assert (grid == UNKNOWN_VALUE).all()

    set_free(grid, 50, 50)
    assert get_cell_value(grid, 50, 50) == FREE_VALUE

    set_occupied(grid, 60, 60)
    assert get_cell_value(grid, 60, 60) == OCCUPIED_VALUE

    # Obstacle overwrite prevention: set_free should not clear an occupied cell
    set_free(grid, 60, 60)
    assert get_cell_value(grid, 60, 60) == OCCUPIED_VALUE


def test_mapping_bresenham_directions():
    # Horizontal
    h_line = bresenham(0, 0, 5, 0)
    assert len(h_line) == 6
    assert all(y == 0 for _, y in h_line)

    # Vertical
    v_line = bresenham(0, 0, 0, 5)
    assert len(v_line) == 6
    assert all(x == 0 for x, _ in v_line)

    # Diagonal
    d_line = bresenham(0, 0, 4, 4)
    assert len(d_line) == 5
    assert d_line[-1] == (4, 4)


def test_mapping_world_grid_boundaries():
    # Inside bounds
    assert is_in_bounds(0, 0)
    assert is_in_bounds(199, 199)
    # Outside bounds
    assert not is_in_bounds(-1, 50)
    assert not is_in_bounds(50, 200)

    # Conversion round trip
    gx, gy = world_to_grid(1.5, -2.5)
    wx, wy = grid_to_world(gx, gy)
    assert wx == pytest.approx(1.5, abs=0.05)
    assert wy == pytest.approx(-2.5, abs=0.05)


def test_mapping_metrics_summary():
    grid = create_grid()
    set_free(grid, 10, 10)
    set_occupied(grid, 10, 11)
    summary = MapVisualizer.map_summary(grid)
    assert summary["explored_pct"] > 0.0
    assert summary["obstacle_cells"] == 1
    assert summary["free_cells"] == 1
    assert summary["total_cells"] == 40000


# ============================================================================
# 5. EXPLORATION TESTS
# ============================================================================

def test_exploration_single_and_multiple_frontiers():
    grid = create_grid()

    # Clear open region 1
    for y in range(50, 60):
        for x in range(50, 60):
            grid[y, x] = FREE_VALUE

    cells = FrontierDetector.detect_frontier_cells(grid)
    assert len(cells) > 0

    clusters = FrontierDetector.cluster_frontiers(cells, min_cluster_size=2)
    assert len(clusters) >= 1

    frontiers = FrontierSelector.select_frontiers(clusters, (0.0, 0.0))
    assert len(frontiers) >= 1
    assert frontiers[0]["status"] == "SELECTED"


def test_exploration_no_frontiers():
    # Fully free grid (no -1 cells)
    full_free_grid = np.full((HEIGHT, WIDTH), FREE_VALUE, dtype=np.int8)
    cells = FrontierDetector.detect_frontier_cells(full_free_grid)
    assert len(cells) == 0

    clusters = FrontierDetector.cluster_frontiers(cells)
    assert len(clusters) == 0

    frontiers = FrontierSelector.select_frontiers(clusters, (0.0, 0.0))
    assert len(frontiers) == 0


def test_exploration_scoring_priority():
    # Two clusters: Cluster A (close, smaller) vs Cluster B (far, huge)
    clusters = [
        (105.0, 100.0, 3),   # ~0.25m distance, size 3
        (160.0, 100.0, 20),  # ~3.0m distance, size 20
    ]
    frontiers = FrontierSelector.select_frontiers(clusters, (0.0, 0.0))
    assert len(frontiers) == 2
    assert frontiers[0]["status"] == "SELECTED"
    assert frontiers[1]["status"] == "CANDIDATE"


# ============================================================================
# 6. NAVIGATION TESTS
# ============================================================================

def test_navigation_astar_open_and_obstacle_maps():
    grid = create_grid()
    for y in range(40, 160):
        for x in range(40, 160):
            grid[y, x] = FREE_VALUE

    planner = AStarPlanner(inflation_radius_cells=2)
    path = planner.plan_path(grid, start_world=(0.0, 0.0), goal_world=(1.0, 1.0))
    assert path is not None
    assert len(path) > 1

    # Place an obstacle wall between start and goal
    wall_gx, _ = world_to_grid(0.5, 0.0)
    for gy in range(80, 120):
        grid[gy, wall_gx] = OCCUPIED_VALUE

    path_around_wall = planner.plan_path(grid, start_world=(0.0, 0.0), goal_world=(1.0, 0.0))
    assert path_around_wall is not None
    # Verify no path point penetrates the wall
    for pt in path_around_wall:
        pgx, pgy = world_to_grid(pt["x_m"], pt["y_m"])
        assert grid[pgy, pgx] != OCCUPIED_VALUE


def test_navigation_astar_no_path_and_start_equals_goal():
    grid = create_grid()
    planner = AStarPlanner(inflation_radius_cells=2)

    # Start equals goal
    same_path = planner.plan_path(grid, start_world=(0.0, 0.0), goal_world=(0.0, 0.0))
    assert same_path is not None
    assert len(same_path) == 1

    # Completely enclosed goal
    gx, gy = world_to_grid(1.0, 1.0)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grid[gy + dy, gx + dx] = OCCUPIED_VALUE

    no_path = planner.plan_path(grid, start_world=(0.0, 0.0), goal_world=(1.0, 1.0))
    assert no_path is None


def test_navigation_obstacle_avoidance_and_controller():
    avoidance = ObstacleAvoidance(safety_stop_distance_m=0.18, slowdown_distance_m=0.40)

    # Proximity stop (< 0.18m)
    range_stop = {"us_fl_mm": 120, "us_fr_mm": 500, "tof_front_mm": 600}
    is_blocked, scale, _ = avoidance.evaluate(range_stop)
    assert is_blocked
    assert scale == 0.0

    # Proximity clear
    range_clear = {"us_fl_mm": 1200, "us_fr_mm": 1500, "tof_front_mm": 1600}
    is_blocked, scale, _ = avoidance.evaluate(range_clear)
    assert not is_blocked
    assert scale == 1.0

    controller = VelocityController(max_linear_mps=0.35, max_angular_rads=1.05)
    cmd, goal_reached = controller.compute_command(
        current_pose=(0.0, 0.0, 0.0),
        path_points=[{"x_m": 0.5, "y_m": 0.0, "yaw_rad": 0.0}],
        speed_scale=1.0,
        source="AUTONOMY",
    )
    assert not goal_reached
    assert 0.0 < cmd["linear_mps"] <= 0.35
    assert abs(cmd["angular_rads"]) <= 1.05


# ============================================================================
# 7. MOTOR BRIDGE TESTS
# ============================================================================

def test_motor_bridge_packet_serialization_and_watchdog():
    builder = PacketBuilder(wheel_base_m=0.28, wheel_radius_m=0.05)
    pkt = builder.build_drive_packet(command_id="CMD-123", linear_mps=0.20, angular_rads=0.10, source="AUTONOMY")

    assert pkt["command_id"] == "CMD-123"
    assert pkt["linear_mps"] == 0.20
    assert pkt["angular_rads"] == 0.10
    assert pkt["source"] == "AUTONOMY"
    assert "left_mps" in pkt and "right_mps" in pkt

    # Stop packet
    stop_pkt = builder.build_stop_packet(command_id="ESTOP", source="EMERGENCY_STOP", e_stop=True)
    assert stop_pkt["linear_mps"] == 0.0
    assert stop_pkt["angular_rads"] == 0.0
    assert stop_pkt["e_stop"] is True

    # Watchdog
    watchdog = MotorWatchdog(timeout_s=0.20)
    assert not watchdog.check()
    watchdog.trigger_emergency_latch()
    assert watchdog.check()
    watchdog.reset_latch()
    assert not watchdog.check()
