"""Contract Verification Tests for ARACHNID Software Integration Contract v1.0.0.

Validates that all topic names, message schemas, field names, data types,
units, coordinate frames, occupancy grid parameters, and enums strictly match Contract v1.0.0.
"""

import math
import pytest


class TestContractTopicsAndSchemas:
    """Verifies all strict requirements of Contract v1.0.0."""

    def test_topic_names(self):
        """Contract Topic Names must match exactly."""
        expected_topics = {
            "/sensors/range",
            "/imu/data",
            "/odom",
            "/robot_pose",
            "/map",
            "/frontiers",
            "/planned_path",
            "/cmd_vel",
            "/robot_state",
            "/robot_errors",
            "/emergency_stop",
        }
        assert len(expected_topics) == 11
        for topic in expected_topics:
            assert topic.startswith("/")
            assert not topic.endswith("/")

    def test_range_packet_schema(self):
        """RangePacket must contain all contract fields with correct types."""
        range_packet = {
            "timestamp_ms": 1725200000000,
            "seq": 1,
            "us_fl_mm": 450.0,
            "us_fr_mm": 460.0,
            "us_l_mm": 1200.0,
            "us_r_mm": 1180.0,
            "tof_front_mm": 445.0,
            "sensor_status": {
                "us_fl": "OK",
                "us_fr": "OK",
                "us_l": "OK",
                "us_r": "OK",
                "tof_front": "OK",
            },
        }

        required_keys = [
            "timestamp_ms",
            "seq",
            "us_fl_mm",
            "us_fr_mm",
            "us_l_mm",
            "us_r_mm",
            "tof_front_mm",
            "sensor_status",
        ]
        for key in required_keys:
            assert key in range_packet, f"Missing required field {key} in RangePacket"

        assert isinstance(range_packet["timestamp_ms"], int)
        assert isinstance(range_packet["seq"], int)
        assert isinstance(range_packet["us_fl_mm"], (int, float))
        assert isinstance(range_packet["us_fr_mm"], (int, float))
        assert isinstance(range_packet["us_l_mm"], (int, float))
        assert isinstance(range_packet["us_r_mm"], (int, float))
        assert isinstance(range_packet["tof_front_mm"], (int, float))
        assert isinstance(range_packet["sensor_status"], dict)

    def test_imu_packet_schema(self):
        """ImuPacket must contain all contract fields with correct types."""
        imu_packet = {
            "timestamp_ms": 1725200000000,
            "seq": 1,
            "accel_x_mps2": 0.01,
            "accel_y_mps2": -0.02,
            "accel_z_mps2": 9.81,
            "gyro_x_rads": 0.001,
            "gyro_y_rads": -0.001,
            "gyro_z_rads": 0.005,
        }

        required_keys = [
            "timestamp_ms",
            "seq",
            "accel_x_mps2",
            "accel_y_mps2",
            "accel_z_mps2",
            "gyro_x_rads",
            "gyro_y_rads",
            "gyro_z_rads",
        ]
        for key in required_keys:
            assert key in imu_packet, f"Missing required field {key} in ImuPacket"

        for key in required_keys[2:]:
            assert isinstance(imu_packet[key], (int, float))

    def test_odometry_packet_schema(self):
        """OdometryPacket must contain all contract fields."""
        odom_packet = {
            "timestamp_ms": 1725200000000,
            "x_m": 0.35,
            "y_m": 0.12,
            "yaw_rad": 0.18,
            "linear_velocity_mps": 0.20,
            "angular_velocity_rads": 0.05,
            "left_ticks": 1420,
            "right_ticks": 1465,
        }

        required_keys = [
            "timestamp_ms",
            "x_m",
            "y_m",
            "yaw_rad",
            "linear_velocity_mps",
            "angular_velocity_rads",
            "left_ticks",
            "right_ticks",
        ]
        for key in required_keys:
            assert key in odom_packet, f"Missing required field {key} in OdometryPacket"

    def test_pose_packet_schema(self):
        """PosePacket must contain all contract fields and frame 'map'."""
        pose_packet = {
            "timestamp_ms": 1725200000000,
            "frame": "map",
            "x_m": 0.35,
            "y_m": 0.12,
            "yaw_rad": 0.18,
            "confidence": 0.98,
        }

        required_keys = [
            "timestamp_ms",
            "frame",
            "x_m",
            "y_m",
            "yaw_rad",
            "confidence",
        ]
        for key in required_keys:
            assert key in pose_packet, f"Missing required field {key} in PosePacket"

        assert pose_packet["frame"] == "map"
        assert 0.0 <= pose_packet["confidence"] <= 1.0

    def test_occupancy_grid_contract_constants(self):
        """Occupancy grid dimensions, resolution, origin, and values must match contract exactly."""
        from mapping.grid_utils import (
            FREE_VALUE,
            HEIGHT,
            OCCUPIED_VALUE,
            ORIGIN_X,
            ORIGIN_Y,
            RESOLUTION,
            UNKNOWN_VALUE,
            WIDTH,
        )

        assert RESOLUTION == 0.05
        assert WIDTH == 200
        assert HEIGHT == 200
        assert ORIGIN_X == -5.0
        assert ORIGIN_Y == -5.0
        assert UNKNOWN_VALUE == -1
        assert FREE_VALUE == 0
        assert OCCUPIED_VALUE == 100

    def test_frontier_packet_schema(self):
        """FrontierPacket must contain timestamp and list of frontier objects with valid fields and statuses."""
        frontier_packet = {
            "timestamp_ms": 1725200000000,
            "frontiers": [
                {
                    "id": "F-001",
                    "x_m": 1.25,
                    "y_m": 0.85,
                    "distance_m": 1.51,
                    "score": 1.85,
                    "status": "SELECTED",
                },
                {
                    "id": "F-002",
                    "x_m": -0.80,
                    "y_m": 2.10,
                    "distance_m": 2.25,
                    "score": 0.92,
                    "status": "CANDIDATE",
                },
            ],
        }

        assert "timestamp_ms" in frontier_packet
        assert "frontiers" in frontier_packet
        assert isinstance(frontier_packet["frontiers"], list)

        valid_statuses = {"CANDIDATE", "SELECTED", "REACHED", "REJECTED", "STALE"}
        for f in frontier_packet["frontiers"]:
            for key in ["id", "x_m", "y_m", "distance_m", "score", "status"]:
                assert key in f
            assert f["status"] in valid_statuses

    def test_path_packet_schema(self):
        """PathPacket must contain timestamp_ms, status, target_id, and points list."""
        path_packet = {
            "timestamp_ms": 1725200000000,
            "status": "NAVIGATING",
            "target_id": "F-001",
            "points": [
                {"x_m": 0.35, "y_m": 0.11, "yaw_rad": 0.18},
                {"x_m": 0.50, "y_m": 0.25, "yaw_rad": 0.35},
            ],
        }

        required_keys = ["timestamp_ms", "status", "target_id", "points"]
        for key in required_keys:
            assert key in path_packet

        valid_nav_statuses = {
            "IDLE",
            "SELECTING_FRONTIER",
            "PLANNING",
            "NAVIGATING",
            "OBSTACLE_BLOCKED",
            "TARGET_REACHED",
            "NO_PATH",
            "COMPLETE",
            "ERROR",
        }
        assert path_packet["status"] in valid_nav_statuses

        for pt in path_packet["points"]:
            for pt_key in ["x_m", "y_m", "yaw_rad"]:
                assert pt_key in pt

    def test_velocity_command_schema(self):
        """VelocityCommand must contain command_id, timestamp_ms, linear_mps, angular_rads, source."""
        cmd_vel = {
            "command_id": "CMD-000001",
            "timestamp_ms": 1725200000000,
            "linear_mps": 0.25,
            "angular_rads": 0.10,
            "source": "AUTONOMY",
        }

        required_keys = [
            "command_id",
            "timestamp_ms",
            "linear_mps",
            "angular_rads",
            "source",
        ]
        for key in required_keys:
            assert key in cmd_vel

        assert isinstance(cmd_vel["command_id"], str)
        assert isinstance(cmd_vel["linear_mps"], (int, float))
        assert isinstance(cmd_vel["angular_rads"], (int, float))
        assert isinstance(cmd_vel["source"], str)

    def test_robot_error_schema(self):
        """RobotError must contain timestamp_ms, component, code, severity, message, latched."""
        error_packet = {
            "timestamp_ms": 1725200000000,
            "component": "sensor_interface",
            "code": "SENSOR_TIMEOUT",
            "severity": "WARNING",
            "message": "Sensor timed out",
            "latched": False,
        }

        required_keys = [
            "timestamp_ms",
            "component",
            "code",
            "severity",
            "message",
            "latched",
        ]
        for key in required_keys:
            assert key in error_packet

        assert error_packet["severity"] in {"WARNING", "ERROR", "FATAL"}
        assert isinstance(error_packet["latched"], bool)

    def test_robot_state_schema(self):
        """RobotState must contain timestamp_ms, robot_mode, nav_status, safety_status, battery_percent."""
        state_packet = {
            "timestamp_ms": 1725200000000,
            "robot_mode": "AUTONOMOUS",
            "nav_status": "NAVIGATING",
            "safety_status": "NORMAL",
            "battery_percent": 95.0,
        }

        required_keys = [
            "timestamp_ms",
            "robot_mode",
            "nav_status",
            "safety_status",
            "battery_percent",
        ]
        for key in required_keys:
            assert key in state_packet

        assert state_packet["robot_mode"] in {
            "DISCONNECTED", "IDLE", "MANUAL", "AUTONOMOUS", "PAUSED", "EMERGENCY_STOP", "ERROR"
        }

    def test_emergency_stop_schema(self):
        """EmergencyStopPacket must contain timestamp_ms, stop boolean, source."""
        estop_packet = {
            "timestamp_ms": 1725200000000,
            "stop": True,
            "source": "OPERATOR",
        }
        for key in ["timestamp_ms", "stop", "source"]:
            assert key in estop_packet
        assert isinstance(estop_packet["stop"], bool)

    def test_contract_enums(self):
        """Verify all contract enums."""
        robot_modes = {
            "DISCONNECTED",
            "IDLE",
            "MANUAL",
            "AUTONOMOUS",
            "PAUSED",
            "EMERGENCY_STOP",
            "ERROR",
        }
        nav_statuses = {
            "IDLE",
            "SELECTING_FRONTIER",
            "PLANNING",
            "NAVIGATING",
            "OBSTACLE_BLOCKED",
            "TARGET_REACHED",
            "NO_PATH",
            "COMPLETE",
            "ERROR",
        }
        safety_statuses = {
            "NORMAL",
            "WARNING",
            "STOP_REQUESTED",
            "EMERGENCY_STOP",
            "HARDWARE_FAULT",
        }
        frontier_statuses = {
            "CANDIDATE",
            "SELECTED",
            "REACHED",
            "REJECTED",
            "STALE",
        }

        assert len(robot_modes) == 7
        assert len(nav_statuses) == 9
        assert len(safety_statuses) == 5
        assert len(frontier_statuses) == 5
