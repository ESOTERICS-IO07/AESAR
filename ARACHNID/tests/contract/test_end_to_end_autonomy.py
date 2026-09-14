"""End-to-End Autonomy Pipeline Verification Tests.

Simulates exploration, mapping progression, multi-timestep navigation,
and emergency stop overrides across all Person A modules.
"""

import math
import numpy as np
import pytest

from exploration.frontier_detector import FrontierDetector
from exploration.frontier_selector import FrontierSelector
from localization.complementary_filter import ComplementaryFilter
from localization.pose_estimator import PoseEstimator
from mapping.grid_utils import (
    FREE_VALUE,
    HEIGHT,
    OCCUPIED_VALUE,
    WIDTH,
    create_grid,
    grid_to_world,
    set_free,
    set_occupied,
    world_to_grid,
)
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
from sensor_interface.serial_parser import (
    ImuPacketValidator,
    RangePacketValidator,
)
from motor_bridge.packet_builder import PacketBuilder


def test_full_person_a_autonomy_cycle():
    """Verify single-cycle end-to-end data pipeline from sensors to motor outputs."""

    # 1. SENSOR INTERFACE
    range_packet = RangePacketValidator.build_packet(
        seq=100,
        us_fc_mm=850.0, us_fl_mm=850.0,
        us_fr_mm=860.0,
        us_l_mm=1200.0,
        us_r_mm=1180.0,
        tof_front_mm=840.0,
    )
    assert RangePacketValidator.validate(range_packet)

    imu_packet = ImuPacketValidator.build_packet(
        seq=100,
        accel_x_mps2=0.02,
        accel_y_mps2=0.00,
        accel_z_mps2=9.81,
        gyro_x_rads=0.0,
        gyro_y_rads=0.0,
        gyro_z_rads=0.05,
    )
    assert ImuPacketValidator.validate(imu_packet)

    # 2. ODOMETRY
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(left_ticks=1000, right_ticks=1000)

    (odom_x, odom_y, odom_yaw), (v_lin, v_ang) = em.update_pose(
        current_left_ticks=1180,
        current_right_ticks=1180,
        current_pose=(0.0, 0.0, 0.0),
        dt=0.5,
    )
    assert odom_x > 0.1
    assert v_lin > 0.0

    imu_fuse = IMUFusion(alpha=0.9)
    imu_fuse.reset(0.0)
    fused_yaw = imu_fuse.update(gyro_z_rads=0.05, encoder_yaw_rad=odom_yaw, dt=0.5)

    odom_packet = {
        "timestamp_ms": 1725200000000,
        "x_m": round(odom_x, 3),
        "y_m": round(odom_y, 3),
        "yaw_rad": round(fused_yaw, 3),
        "linear_velocity_mps": round(v_lin, 3),
        "angular_velocity_rads": round(v_ang, 3),
        "left_ticks": 1180,
        "right_ticks": 1180,
    }

    # 3. LOCALIZATION
    loc_filter = ComplementaryFilter(alpha=0.95)
    loc_filter.reset(0.0)
    loc_yaw = loc_filter.update(gyro_z_rads=0.05, odom_yaw_rad=odom_packet["yaw_rad"], dt=0.5)

    pose_est = PoseEstimator(frame="map")
    pose_packet = pose_est.update(
        odom_packet=odom_packet,
        fused_yaw=loc_yaw,
        last_update_age_s=0.02,
    )
    assert pose_packet["frame"] == "map"
    assert pose_packet["confidence"] >= 0.9

    # 4. MAPPING
    grid = create_grid()
    robot_x = pose_packet["x_m"]
    robot_y = pose_packet["y_m"]
    robot_yaw = pose_packet["yaw_rad"]

    # Raycast front ToF sensor
    dist_m = range_packet["tof_front_mm"] / 1000.0
    sx, sy, syaw = transform_sensor_to_world(robot_x, robot_y, robot_yaw, 0.16, 0.0, 0.0)
    ex, ey = sensor_endpoint(sx, sy, syaw, dist_m)

    gx0, gy0 = world_to_grid(sx, sy)
    gx1, gy1 = world_to_grid(ex, ey)
    ray_cells = bresenham(gx0, gy0, gx1, gy1)

    for cx, cy in ray_cells[:-1]:
        set_free(grid, cx, cy)
    set_occupied(grid, ray_cells[-1][0], ray_cells[-1][1])

    assert grid[ray_cells[-1][1], ray_cells[-1][0]] == OCCUPIED_VALUE

    # Clear open surrounding space to produce exploreable frontiers
    for y in range(gy0 - 15, gy0 + 15):
        for x in range(gx0 - 15, gx0 + 15):
            if grid[y, x] != OCCUPIED_VALUE:
                grid[y, x] = FREE_VALUE

    # 5. EXPLORATION
    frontier_cells = FrontierDetector.detect_frontier_cells(grid)
    assert len(frontier_cells) > 0

    clusters = FrontierDetector.cluster_frontiers(frontier_cells, min_cluster_size=2)
    assert len(clusters) > 0

    frontiers = FrontierSelector.select_frontiers(clusters, (robot_x, robot_y))
    assert len(frontiers) > 0
    selected_frontier = frontiers[0]
    assert selected_frontier["status"] == "SELECTED"

    # 6. NAVIGATION (A* Planning)
    planner = AStarPlanner(inflation_radius_cells=2)
    start_point = (robot_x, robot_y)
    goal_point = (selected_frontier["x_m"], selected_frontier["y_m"])

    path = planner.plan_path(grid, start_point, goal_point)
    assert path is not None
    assert len(path) > 0

    # 7. NAVIGATION (Obstacle Avoidance & Velocity Control)
    avoidance = ObstacleAvoidance(safety_stop_distance_m=0.18, slowdown_distance_m=0.40)
    is_blocked, speed_scale, reason = avoidance.evaluate(range_packet)
    assert not is_blocked

    controller = VelocityController(max_linear_mps=0.35, max_angular_rads=1.05)
    cmd_vel, goal_reached = controller.compute_command(
        current_pose=(robot_x, robot_y, robot_yaw),
        path_points=path,
        speed_scale=speed_scale,
        source="AUTONOMY",
    )
    assert cmd_vel["source"] == "AUTONOMY"
    assert "linear_mps" in cmd_vel
    assert "angular_rads" in cmd_vel

    # 8. MOTOR BRIDGE KINEMATICS
    v = cmd_vel["linear_mps"]
    w = cmd_vel["angular_rads"]
    wheel_base = 0.28
    v_left = v - (w * wheel_base / 2.0)
    v_right = v + (w * wheel_base / 2.0)

    assert isinstance(v_left, float)
    assert isinstance(v_right, float)


def test_multistep_exploration_and_mapping_progression():
    """Simulate 10 continuous timesteps of autonomous mapping progression."""
    grid = create_grid()
    rx, ry, ryaw = 0.0, 0.0, 0.0
    em = EncoderMath()
    em.reset(0, 0)

    ticks = 0
    for step in range(10):
        # Step forward
        ticks += 36
        (rx, ry, ryaw), (v_lin, _) = em.update_pose(ticks, ticks, (rx, ry, ryaw), dt=0.1)

        # Clear area in front
        gx, gy = world_to_grid(rx, ry)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                set_free(grid, gx + dx, gy + dy)

        # Detect frontiers
        frontier_cells = FrontierDetector.detect_frontier_cells(grid)
        assert len(frontier_cells) > 0

    assert ticks == 360
    assert rx > 0.1


def test_emergency_stop_pipeline_override():
    """Verify that emergency stop overrides path planning and sends immediate zero velocities."""
    builder = PacketBuilder()
    stop_cmd = builder.build_stop_packet(command_id="ESTOP-OVERRIDE", source="EMERGENCY_STOP", e_stop=True)

    assert stop_cmd["linear_mps"] == 0.0
    assert stop_cmd["angular_rads"] == 0.0
    assert stop_cmd["left_mps"] == 0.0
    assert stop_cmd["right_mps"] == 0.0
    assert stop_cmd["e_stop"] is True
