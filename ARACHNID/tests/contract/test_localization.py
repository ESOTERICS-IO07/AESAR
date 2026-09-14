"""Unit & Contract Tests for localization package."""

import pytest
from localization.complementary_filter import ComplementaryFilter
from localization.pose_estimator import PoseEstimator


def test_localization_complementary_filter():
    filt = ComplementaryFilter(alpha=0.95)
    filt.reset(0.0)

    # Initial update
    fused_yaw = filt.update(gyro_z_rads=0.2, odom_yaw_rad=0.01, dt=0.05)
    assert isinstance(fused_yaw, float)
    assert -3.15 <= fused_yaw <= 3.15


def test_pose_estimator():
    estimator = PoseEstimator(frame="map")

    odom_packet = {
        "timestamp_ms": 1725200000000,
        "x_m": 1.25,
        "y_m": 0.75,
        "yaw_rad": 0.50,
        "linear_velocity_mps": 0.2,
        "angular_velocity_rads": 0.1,
        "left_ticks": 100,
        "right_ticks": 100,
    }

    pose_packet = estimator.update(
        odom_packet=odom_packet,
        fused_yaw=0.52,
        last_update_age_s=0.05,
    )

    assert pose_packet["frame"] == "map"
    assert pose_packet["x_m"] == 1.25
    assert pose_packet["y_m"] == 0.75
    assert pose_packet["yaw_rad"] == 0.52
    assert 0.0 <= pose_packet["confidence"] <= 1.0
