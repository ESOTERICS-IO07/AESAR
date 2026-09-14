from __future__ import annotations

import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.models.schemas import (
    ExplorationData,
    MapData,
    NavigationData,
    Point2D,
    SensorStatus,
    SensorStatusData,
    Telemetry,
)
from backend.hardware.adapters import SensorAdapter
from backend.hardware.simulator.scenarios import SimulationScenario


class SimulationEngine:
    """
    Kinematic & Environmental Simulator for ARACHNID Rover.

    Simulates:
    - Differential drive kinematics (x, y, heading)
    - 5x Distance sensors ray-casting against simulated obstacles
    - Occupancy grid exploration map
    - Navigation path execution
    - Frontier discovery metrics
    - Failure and stress scenario injections
    """

    def __init__(self) -> None:
        self.scenario: SimulationScenario = SimulationScenario.NORMAL

        # Kinematic state
        self.x: float = 0.0
        self.y: float = 0.0
        self.theta: float = 0.0  # radians
        self.linear_velocity: float = 0.0
        self.angular_velocity: float = 0.0
        self.battery_percent: float = 85.0

        # Map state (20x20 grid, 0.05m/cell => 1m x 1m local grid)
        self.map_width = 20
        self.map_height = 20
        self.map_resolution = 0.05
        self.grid_data: List[int] = [0] * (self.map_width * self.map_height)

        # Place initial obstacles in map
        self._init_obstacles()

        # Navigation state
        self.nav_status: str = "IDLE"
        self.current_goal: Optional[Point2D] = None
        self.planned_path: List[Point2D] = []

        # Exploration state
        self.explored_percent: float = 12.0
        self.frontier_count: int = 5
        self.exploration_target: Optional[Point2D] = Point2D(x=1.5, y=1.2)

        self._seq = 0
        self._last_update = time.time()

    def _init_obstacles(self) -> None:
        # Generate simulated obstacles at perimeter
        for r in range(self.map_height):
            for c in range(self.map_width):
                if r == 0 or r == self.map_height - 1 or c == 0 or c == self.map_width - 1:
                    self.grid_data[r * self.map_width + c] = 100
                elif (r == 12 and 5 <= c <= 9) or (c == 14 and 4 <= r <= 8):
                    self.grid_data[r * self.map_width + c] = 100
                else:
                    self.grid_data[r * self.map_width + c] = 0

    def set_scenario(self, scenario: SimulationScenario) -> None:
        self.scenario = scenario
        if scenario == SimulationScenario.LOW_BATTERY:
            self.battery_percent = 12.0
        elif scenario == SimulationScenario.NORMAL:
            if self.battery_percent < 20.0:
                self.battery_percent = 85.0

    def set_velocity_target(self, linear_mps: float, angular_rads: float) -> None:
        self.linear_velocity = linear_mps
        self.angular_velocity = angular_rads

    def update_physics(self, dt: float) -> None:
        """
        Advance simulated kinematic physics step.
        """
        if self.scenario == SimulationScenario.EMERGENCY_STOP:
            self.linear_velocity = 0.0
            self.angular_velocity = 0.0
            return

        # Kinematics update
        self.theta += self.angular_velocity * dt
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi

        self.x += self.linear_velocity * math.cos(self.theta) * dt
        self.y += self.linear_velocity * math.sin(self.theta) * dt

        # Natural slow battery drain
        if self.scenario != SimulationScenario.LOW_BATTERY:
            self.battery_percent = max(5.0, self.battery_percent - 0.005 * dt)

        # Autonomous exploration progress
        if self.linear_velocity > 0:
            self.explored_percent = min(98.5, self.explored_percent + 0.1 * dt)
            if random.random() < 0.05:
                self.frontier_count = max(0, self.frontier_count + random.choice([-1, 0, 1]))

    def get_simulated_sensors(self) -> Dict[str, Any]:
        """
        Calculate distance readings for 4x Ultrasonic + 1x ToF based on scenario & position.
        """
        now_ms = int(time.time() * 1000)

        # Base noise
        noise = random.uniform(-15.0, 15.0)

        # Environmental simulation
        temp = round(24.0 + 3.0 * math.sin(self.x * 0.5) + random.uniform(-0.3, 0.3), 1)
        hum = round(65.0 + 5.0 * math.cos(self.y * 0.5) + random.uniform(-0.5, 0.5), 1)
        sm_pct = max(10.0, min(90.0, 45.0 + 10.0 * math.sin((self.x + self.y) * 0.3) + random.uniform(-1.0, 1.0)))
        raw_adc = int(3200 - (sm_pct / 100.0) * (3200 - 1400))
        env_data = {
            "temperature_c": temp,
            "humidity_percent": hum,
            "soil_moisture_raw": raw_adc,
        }

        if self.scenario == SimulationScenario.OBSTACLE_AHEAD:
            res = {
                "timestamp_ms": now_ms,
                "us_fl_mm": 280.0 + noise,
                "us_fr_mm": 270.0 + noise,
                "us_l_mm": 1100.0 + noise,
                "us_r_mm": 1200.0 + noise,
                "tof_front_mm": 220.0 + noise,
            }
        elif self.scenario == SimulationScenario.OBSTACLE_LEFT:
            res = {
                "timestamp_ms": now_ms,
                "us_fl_mm": 350.0 + noise,
                "us_fr_mm": 1400.0 + noise,
                "us_l_mm": 220.0 + noise,
                "us_r_mm": 1500.0 + noise,
                "tof_front_mm": 950.0 + noise,
            }
        elif self.scenario == SimulationScenario.OBSTACLE_RIGHT:
            res = {
                "timestamp_ms": now_ms,
                "us_fl_mm": 1400.0 + noise,
                "us_fr_mm": 340.0 + noise,
                "us_l_mm": 1600.0 + noise,
                "us_r_mm": 210.0 + noise,
                "tof_front_mm": 980.0 + noise,
            }
        elif self.scenario == SimulationScenario.SENSOR_FAILURE:
            res = {
                "timestamp_ms": now_ms,
                "us_fl_mm": -1.0,  # Disconnected
                "us_fr_mm": 950.0 + noise,
                "us_l_mm": 760.0 + noise,
                "us_r_mm": 5500.0,  # Out of range
                "tof_front_mm": 880.0 + noise,
            }
        elif self.scenario == SimulationScenario.SENSOR_TIMEOUT:
            res = {
                "timestamp_ms": now_ms - 5000,  # Stale timestamp > 3000ms
                "us_fl_mm": -1.0,
                "us_fr_mm": -1.0,
                "us_l_mm": -1.0,
                "us_r_mm": -1.0,
                "tof_front_mm": -1.0,
            }
        else:
            # Normal scenario with dynamic distance modulation based on position
            base_front = 1100.0 + math.sin(self.x * 2.0) * 300.0 + noise
            base_left = 850.0 + math.cos(self.y * 2.0) * 200.0 + noise
            base_right = 950.0 - math.cos(self.y * 2.0) * 150.0 + noise

            res = {
                "timestamp_ms": now_ms,
                "us_fl_mm": max(100.0, base_front + 80.0),
                "us_fr_mm": max(100.0, base_front - 60.0),
                "us_l_mm": max(100.0, base_left),
                "us_r_mm": max(100.0, base_right),
                "tof_front_mm": max(50.0, base_front - 150.0),
            }

        res.update(env_data)
        return res

    def get_telemetry_model(self, seq: int) -> Telemetry:
        raw = self.get_simulated_sensors()
        return SensorAdapter.convert_raw_telemetry(raw, seq)

    def get_map_model(self) -> MapData:
        return MapData(
            resolution_m_per_cell=self.map_resolution,
            width=self.map_width,
            height=self.map_height,
            origin=Point2D(x=round(self.x, 2), y=round(self.y, 2)),
            data=self.grid_data,
        )

    def get_navigation_model(self) -> NavigationData:
        if self.scenario == SimulationScenario.NAVIGATION_FAILURE:
            return NavigationData(
                status="FAILED",
                goal=Point2D(x=2.5, y=3.0),
                path=[],
            )

        if self.current_goal:
            path = [
                Point2D(x=round(self.x, 2), y=round(self.y, 2)),
                Point2D(x=round((self.x + self.current_goal.x) / 2, 2), y=round((self.y + self.current_goal.y) / 2, 2)),
                self.current_goal,
            ]
            return NavigationData(status="NAVIGATING", goal=self.current_goal, path=path)

        return NavigationData(
            status="IDLE",
            goal=Point2D(x=0.0, y=0.0),
            path=[],
        )

    def get_exploration_model(self) -> ExplorationData:
        if self.scenario == SimulationScenario.EXPLORATION_FAILURE:
            return ExplorationData(
                status="FAILED",
                explored_percent=self.explored_percent,
                frontier_count=0,
                current_goal=None,
            )

        return ExplorationData(
            status="EXPLORING",
            explored_percent=round(self.explored_percent, 1),
            frontier_count=self.frontier_count,
            current_goal=self.exploration_target,
        )
