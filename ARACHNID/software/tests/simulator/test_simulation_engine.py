import math
import pytest
from backend.models.schemas import SensorStatus
from backend.hardware.simulator.engine import SimulationEngine
from backend.hardware.simulator.scenarios import SimulationScenario


def test_simulation_engine_kinematics():
    engine = SimulationEngine()
    engine.set_velocity_target(0.5, 0.0)  # Move forward at 0.5 m/s

    engine.update_physics(1.0)  # 1 second step
    assert math.isclose(engine.x, 0.5, abs_tol=0.01)
    assert math.isclose(engine.y, 0.0, abs_tol=0.01)

    # Rotate left
    engine.set_velocity_target(0.0, 1.57)  # approx 90 deg/s
    engine.update_physics(1.0)
    assert engine.theta > 1.0


def test_simulation_engine_sensor_readings():
    engine = SimulationEngine()
    sensors = engine.get_simulated_sensors()

    assert "us_fl_mm" in sensors
    assert "us_fr_mm" in sensors
    assert "us_l_mm" in sensors
    assert "us_r_mm" in sensors
    assert "tof_front_mm" in sensors
    assert sensors["us_fl_mm"] > 0
    assert sensors["tof_front_mm"] > 0


def test_scenario_obstacle_ahead():
    engine = SimulationEngine()
    engine.set_scenario(SimulationScenario.OBSTACLE_AHEAD)

    sensors = engine.get_simulated_sensors()
    assert sensors["us_fl_mm"] < 350.0
    assert sensors["us_fr_mm"] < 350.0
    assert sensors["tof_front_mm"] < 300.0


def test_scenario_sensor_failure():
    engine = SimulationEngine()
    engine.set_scenario(SimulationScenario.SENSOR_FAILURE)

    telemetry = engine.get_telemetry_model(1)
    assert telemetry.sensor_status.us_fl == SensorStatus.DISCONNECTED
    assert telemetry.sensor_status.us_r == SensorStatus.OUT_OF_RANGE


def test_scenario_low_battery():
    engine = SimulationEngine()
    engine.set_scenario(SimulationScenario.LOW_BATTERY)

    assert engine.battery_percent <= 15.0


def test_scenario_emergency_stop():
    engine = SimulationEngine()
    engine.set_velocity_target(0.5, 0.5)
    engine.set_scenario(SimulationScenario.EMERGENCY_STOP)

    engine.update_physics(1.0)
    assert engine.linear_velocity == 0.0
    assert engine.angular_velocity == 0.0


def test_map_and_navigation_models():
    engine = SimulationEngine()
    map_model = engine.get_map_model()
    assert map_model.width == 20
    assert map_model.height == 20
    assert len(map_model.data) == 400

    nav_model = engine.get_navigation_model()
    assert nav_model.status in ["IDLE", "NAVIGATING"]

    exp_model = engine.get_exploration_model()
    assert exp_model.status in ["IDLE", "EXPLORING"]
    assert exp_model.explored_percent >= 0.0
