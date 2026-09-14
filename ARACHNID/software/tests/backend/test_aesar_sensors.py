from __future__ import annotations

import pytest
from backend.hardware.calibration import SoilMoistureCalibrator
from backend.hardware.adapters import EnvironmentalAdapter, SensorAdapter
from backend.models.schemas import AgriSensorState


def test_soil_moisture_calibration_inverted():
    # Inverted capacitive sensor: dry (3200) -> 0%, wet (1400) -> 100%
    calibrator = SoilMoistureCalibrator(dry_adc=3200, wet_adc=1400, invert=True)

    # Air / Dry
    pct, valid = calibrator.calibrate(3200)
    assert valid is True
    assert pct == 0.0

    # Water / Wet
    pct, valid = calibrator.calibrate(1400)
    assert valid is True
    assert pct == 100.0

    # Midpoint: (3200 + 1400)/2 = 2300 -> 50%
    pct, valid = calibrator.calibrate(2300)
    assert valid is True
    assert pct == 50.0

    # Out of valid ADC range
    pct, valid = calibrator.calibrate(0)
    assert valid is False
    assert pct is None


def test_soil_moisture_calibration_non_inverted():
    calibrator = SoilMoistureCalibrator(dry_adc=1000, wet_adc=3000, invert=False)
    pct, valid = calibrator.calibrate(1000)
    assert valid is True
    assert pct == 0.0

    pct, valid = calibrator.calibrate(3000)
    assert valid is True
    assert pct == 100.0


def test_environmental_adapter_parsing():
    adapter = EnvironmentalAdapter()
    raw = {
        "temperature_c": 26.5,
        "humidity_percent": 68.0,
        "soil_moisture_raw": 2300,
    }
    env = adapter.convert_raw_environment(raw)
    assert env.available is True
    assert env.status == AgriSensorState.AVAILABLE
    assert env.temperature_c == 26.5
    assert env.humidity_percent == 68.0
    assert env.soil_moisture_raw == 2300
    assert env.soil_moisture_percent == 50.0


def test_environmental_adapter_unavailable():
    adapter = EnvironmentalAdapter()
    raw = {}
    env = adapter.convert_raw_environment(raw)
    assert env.available is False
    assert env.status == AgriSensorState.UNAVAILABLE
    assert env.temperature_c is None
    assert env.soil_moisture_percent is None


def test_sensor_adapter_integrates_environment():
    raw_packet = {
        "us_fc_mm": 500.0,
        "temperature_c": 24.0,
        "humidity_percent": 60.0,
        "soil_moisture_raw": 2300,
    }
    telemetry = SensorAdapter.convert_raw_telemetry(raw_packet, 1)
    assert telemetry.environment is not None
    assert telemetry.environment.available is True
    assert telemetry.environment.temperature_c == 24.0
