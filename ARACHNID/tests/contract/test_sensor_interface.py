"""Unit & Contract Tests for sensor_interface package."""

import pytest
from sensor_interface.filter import LowPassFilter, MedianFilter, MovingAverageFilter
from sensor_interface.serial_parser import (
    ImuPacketValidator,
    RangePacketValidator,
    SerialParser,
)


def test_serial_parser_parse_line():
    assert SerialParser.parse_line("") is None
    assert SerialParser.parse_line("   ") is None
    assert SerialParser.parse_line("invalid json") is None

    valid_json = '{"seq": 10, "us_fl_mm": 500.0}'
    parsed = SerialParser.parse_line(valid_json)
    assert parsed is not None
    assert parsed["seq"] == 10
    assert parsed["us_fl_mm"] == 500.0


def test_range_packet_validator():
    invalid_packet = {"timestamp_ms": 123, "seq": 1}
    assert not RangePacketValidator.validate(invalid_packet)

    valid_packet = RangePacketValidator.build_packet(
        seq=1,
        us_fc_mm=850.0, us_fl_mm=450.0,
        us_fr_mm=460.0,
        us_l_mm=1200.0,
        us_r_mm=1180.0,
        tof_front_mm=440.0,
    )
    assert RangePacketValidator.validate(valid_packet)
    assert valid_packet["seq"] == 1
    assert valid_packet["us_fl_mm"] == 450.0
    assert valid_packet["sensor_status"]["tof_front"] == "OK"


def test_imu_packet_validator():
    invalid_packet = {"seq": 1}
    assert not ImuPacketValidator.validate(invalid_packet)

    valid_packet = ImuPacketValidator.build_packet(
        seq=5,
        accel_x_mps2=0.01,
        accel_y_mps2=-0.02,
        accel_z_mps2=9.81,
        gyro_x_rads=0.0,
        gyro_y_rads=0.0,
        gyro_z_rads=0.05,
    )
    assert ImuPacketValidator.validate(valid_packet)
    assert valid_packet["accel_z_mps2"] == 9.81
    assert valid_packet["gyro_z_rads"] == 0.05


def test_median_filter():
    med_filter = MedianFilter(window_size=5)
    # Feed spike sequence
    readings = [100.0, 105.0, 5000.0, 102.0, 103.0]
    results = [med_filter.update(r) for r in readings]
    # Median should reject the 5000.0 spike
    assert results[-1] == 103.0


def test_moving_average_filter():
    ma_filter = MovingAverageFilter(window_size=3)
    ma_filter.update(10.0)
    ma_filter.update(20.0)
    avg = ma_filter.update(30.0)
    assert avg == pytest.approx(20.0)


def test_low_pass_filter():
    lp = LowPassFilter(alpha=0.5)
    # First step
    assert lp.update(10.0) == pytest.approx(10.0)
    # Second step
    assert lp.update(20.0) == pytest.approx(15.0)
