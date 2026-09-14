from __future__ import annotations

from threading import RLock

from backend.models.schemas import (
    RoverMode,
    RoverState,
    RoverStatus,
    Telemetry,
    Pose2D,
)


class RoverStateManager:
    def __init__(self) -> None:
        self._lock = RLock()

        self._connected = False
        self._state = RoverState.DISCONNECTED
        self._mode = RoverMode.MANUAL
        self._battery_percent = -1.0
        self._telemetry: Telemetry | None = None
        
        # Estimated global pose
        self._pose_x = 0.0
        self._pose_y = 0.0
        self._pose_theta = 0.0

    def set_connected(self, connected: bool) -> None:
        with self._lock:
            self._connected = connected

            if not connected:
                self._state = RoverState.DISCONNECTED
            elif self._state == RoverState.DISCONNECTED:
                self._state = RoverState.IDLE

    def set_mode(self, mode: RoverMode) -> None:
        with self._lock:
            self._mode = mode

            if self._state != RoverState.EMERGENCY_STOP:
                if mode == RoverMode.MANUAL:
                    self._state = RoverState.MANUAL
                else:
                    self._state = RoverState.AUTONOMOUS

    def set_state(self, state: RoverState) -> None:
        with self._lock:
            self._state = state

    def set_battery(self, battery_percent: float) -> None:
        with self._lock:
            self._battery_percent = battery_percent

    def set_telemetry(self, telemetry: Telemetry) -> None:
        with self._lock:
            self._telemetry = telemetry

    def set_pose(self, x: float, y: float, theta: float) -> None:
        with self._lock:
            self._pose_x = x
            self._pose_y = y
            self._pose_theta = theta

    def get_pose(self) -> tuple[float, float, float]:
        with self._lock:
            return self._pose_x, self._pose_y, self._pose_theta

    def get_status(self) -> RoverStatus:
        with self._lock:
            return RoverStatus(
                connected=self._connected,
                state=self._state,
                mode=self._mode,
                battery_percent=self._battery_percent,
                pose=Pose2D(x=self._pose_x, y=self._pose_y, theta=self._pose_theta),
            )

    def get_telemetry(self) -> Telemetry | None:
        with self._lock:
            return self._telemetry

    def emergency_stop(self) -> None:
        with self._lock:
            self._state = RoverState.EMERGENCY_STOP

    def reset_emergency_stop(self) -> None:
        with self._lock:
            # Never automatically resume movement.
            self._state = RoverState.IDLE
            self._mode = RoverMode.MANUAL

    def stop(self) -> None:
        with self._lock:
            if self._state != RoverState.EMERGENCY_STOP:
                self._state = RoverState.IDLE

    def is_emergency_stopped(self) -> bool:
        with self._lock:
            return self._state == RoverState.EMERGENCY_STOP