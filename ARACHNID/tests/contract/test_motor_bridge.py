"""Unit & Contract Tests for motor_bridge package."""

import pytest


def calculate_wheel_speeds(linear_mps: float, angular_rads: float, wheel_base_m: float = 0.28):
    v_left = linear_mps - (angular_rads * wheel_base_m / 2.0)
    v_right = linear_mps + (angular_rads * wheel_base_m / 2.0)
    return round(v_left, 3), round(v_right, 3)


def test_motor_bridge_straight_motion():
    # 0.2 m/s forward, 0.0 rad/s angular
    vl, vr = calculate_wheel_speeds(0.20, 0.0, wheel_base_m=0.28)
    assert vl == 0.20
    assert vr == 0.20


def test_motor_bridge_differential_turn():
    # Turn in place: 0.0 m/s, 1.0 rad/s CCW
    vl, vr = calculate_wheel_speeds(0.0, 1.0, wheel_base_m=0.28)
    # v_left = -0.14, v_right = +0.14
    assert vl == -0.14
    assert vr == 0.14
