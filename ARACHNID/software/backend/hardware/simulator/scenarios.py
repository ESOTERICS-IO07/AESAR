from __future__ import annotations

from enum import Enum


class SimulationScenario(str, Enum):
    """
    Controllable failure and environmental simulation scenarios for ARACHNID.
    Used for pre-physical hardware automated testing and software-only validation.
    """

    NORMAL = "NORMAL"
    OBSTACLE_AHEAD = "OBSTACLE_AHEAD"
    OBSTACLE_LEFT = "OBSTACLE_LEFT"
    OBSTACLE_RIGHT = "OBSTACLE_RIGHT"
    SENSOR_FAILURE = "SENSOR_FAILURE"
    SENSOR_TIMEOUT = "SENSOR_TIMEOUT"
    ROS2_DISCONNECT = "ROS2_DISCONNECT"
    ROS2_RECONNECT = "ROS2_RECONNECT"
    LOW_BATTERY = "LOW_BATTERY"
    NAVIGATION_FAILURE = "NAVIGATION_FAILURE"
    EXPLORATION_FAILURE = "EXPLORATION_FAILURE"
    EMERGENCY_STOP = "EMERGENCY_STOP"
