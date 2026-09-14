"""Unit & Contract Tests for odometry package."""

import math
import pytest
from odometry.encoder_math import EncoderMath, normalize_angle
from odometry.imu_fusion import IMUFusion, shortest_angular_distance


def test_angle_normalization():
    assert normalize_angle(0.0) == pytest.approx(0.0)
    assert normalize_angle(math.pi) == pytest.approx(math.pi)
    assert normalize_angle(3.0 * math.pi) == pytest.approx(math.pi)
    assert normalize_angle(-3.0 * math.pi) == pytest.approx(-math.pi)


def test_shortest_angular_distance():
    # From 3.0 rad to -3.0 rad (across +/- pi boundary)
    diff = shortest_angular_distance(3.0, -3.0)
    assert abs(diff) < 1.0


def test_encoder_ticks_to_distance():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    # One full wheel revolution = 2 * pi * 0.05 m = 0.314159 m
    dist = em.ticks_to_distance(360)
    assert dist == pytest.approx(2.0 * math.pi * 0.05, rel=1e-4)


def test_encoder_straight_line_motion():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(0, 0)

    # Initial state
    current_pose = (0.0, 0.0, 0.0)

    # Move forward: 360 ticks on both wheels over 1.0s
    (new_x, new_y, new_yaw), (v_lin, v_ang) = em.update_pose(
        current_left_ticks=360,
        current_right_ticks=360,
        current_pose=current_pose,
        dt=1.0,
    )

    expected_dist = 2.0 * math.pi * 0.05
    assert new_x == pytest.approx(expected_dist, rel=1e-3)
    assert new_y == pytest.approx(0.0, abs=1e-4)
    assert new_yaw == pytest.approx(0.0, abs=1e-4)
    assert v_lin == pytest.approx(expected_dist, rel=1e-3)
    assert v_ang == pytest.approx(0.0, abs=1e-4)


def test_encoder_pure_rotation():
    em = EncoderMath(wheel_radius_m=0.05, wheel_base_m=0.28, ticks_per_rev=360)
    em.reset(0, 0)

    current_pose = (0.0, 0.0, 0.0)

    # Left ticks = -180, Right ticks = +180
    (new_x, new_y, new_yaw), (v_lin, v_ang) = em.update_pose(
        current_left_ticks=-180,
        current_right_ticks=180,
        current_pose=current_pose,
        dt=1.0,
    )

    assert new_x == pytest.approx(0.0, abs=1e-3)
    assert new_y == pytest.approx(0.0, abs=1e-3)
    assert new_yaw > 0.0  # Counter-clockwise rotation
    assert v_lin == pytest.approx(0.0, abs=1e-3)
    assert v_ang > 0.0


def test_imu_fusion():
    fusion = IMUFusion(alpha=0.9)
    fusion.reset(0.0)

    # Gyro reports 0.1 rad/s for 0.1s => 0.01 rad change
    fused = fusion.update(gyro_z_rads=0.1, encoder_yaw_rad=0.01, dt=0.1)
    assert fused == pytest.approx(0.01, abs=1e-3)
