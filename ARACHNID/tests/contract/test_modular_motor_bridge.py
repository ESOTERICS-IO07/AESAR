"""Unit & Contract Tests for Modular motor_bridge Package."""

import time
import pytest

from motor_bridge.packet_builder import PacketBuilder
from motor_bridge.serial_bridge import SerialBridge
from motor_bridge.watchdog import MotorWatchdog


def test_packet_builder():
    builder = PacketBuilder(wheel_base_m=0.28, wheel_radius_m=0.05)

    # 1. Drive Packet
    packet = builder.build_drive_packet(
        command_id="AUTO-CMD-001",
        linear_mps=0.25,
        angular_rads=0.30,
        source="AUTONOMY",
        e_stop=False,
    )

    required_keys = [
        "command_id",
        "timestamp_ms",
        "linear_mps",
        "angular_rads",
        "left_mps",
        "right_mps",
        "source",
        "e_stop",
    ]
    for key in required_keys:
        assert key in packet

    assert packet["command_id"] == "AUTO-CMD-001"
    assert packet["linear_mps"] == 0.25
    assert packet["angular_rads"] == 0.30
    assert packet["source"] == "AUTONOMY"
    assert not packet["e_stop"]

    # Differential wheel calculations
    # v_left = 0.25 - (0.30 * 0.28 / 2) = 0.25 - 0.042 = 0.208
    # v_right = 0.25 + 0.042 = 0.292
    assert packet["left_mps"] == pytest.approx(0.208, abs=1e-3)
    assert packet["right_mps"] == pytest.approx(0.292, abs=1e-3)

    # 2. Stop Packet
    stop_packet = builder.build_stop_packet(
        command_id="ESTOP-001",
        source="EMERGENCY_STOP",
        e_stop=True,
    )
    assert stop_packet["linear_mps"] == 0.0
    assert stop_packet["angular_rads"] == 0.0
    assert stop_packet["left_mps"] == 0.0
    assert stop_packet["right_mps"] == 0.0
    assert stop_packet["e_stop"] is True


def test_motor_bridge_zero_velocity_packet():
    builder = PacketBuilder(wheel_base_m=0.28, wheel_radius_m=0.05)
    zero_packet = builder.build_drive_packet(
        command_id="CMD-ZERO",
        linear_mps=0.0,
        angular_rads=0.0,
        source="AUTONOMY",
        e_stop=False,
    )
    assert zero_packet["linear_mps"] == 0.0
    assert zero_packet["angular_rads"] == 0.0
    assert zero_packet["left_mps"] == 0.0
    assert zero_packet["right_mps"] == 0.0


def test_motor_watchdog():
    watchdog = MotorWatchdog(timeout_s=0.10)
    assert not watchdog.check()

    # Sleep past timeout
    time.sleep(0.12)
    assert watchdog.check()
    assert watchdog.is_timed_out

    # Kick resets watchdog
    watchdog.kick()
    assert not watchdog.check()
    assert not watchdog.is_timed_out

    # Emergency latch
    watchdog.trigger_emergency_latch()
    assert watchdog.is_latched
    assert watchdog.check()

    # Reset latch
    watchdog.reset_latch()
    assert not watchdog.is_latched
    assert not watchdog.check()


def test_serial_bridge_mock_mode():
    bridge = SerialBridge(port="COM5", baudrate=115200, mock_mode=True)
    assert bridge.is_connected

    packet = {"test": 123}
    success = bridge.send_packet(packet)
    assert success is True

    bridge.close()
