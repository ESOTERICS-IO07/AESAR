"""ARACHNID Motor Bridge Safety Watchdog.

Enforces 500ms command heartbeat timeout. If velocity commands cease,
triggers automatic zero-velocity stop and latches safety state.
"""

from typing import Optional
import time


class MotorWatchdog:
    """Monitors heartbeat interval for incoming velocity commands."""

    def __init__(self, timeout_s: float = 0.50):
        self.timeout_s = float(timeout_s)
        self.last_heartbeat_time = time.time()
        self.is_timed_out = False
        self.is_latched = False

    def kick(self) -> None:
        """Reset the watchdog heartbeat on valid command arrival."""
        self.last_heartbeat_time = time.time()
        self.is_timed_out = False

    def check(self) -> bool:
        """Check if heartbeat expired or emergency is latched.

        Returns:
            True if watchdog has timed out or latched (unsafe), False if healthy.
        """
        if self.is_latched:
            self.is_timed_out = True
            return True

        now = time.time()
        elapsed = now - self.last_heartbeat_time

        if elapsed > self.timeout_s:
            self.is_timed_out = True
            return True
        return False

    def trigger_emergency_latch(self) -> None:
        """Manually latch emergency stop state."""
        self.is_latched = True
        self.is_timed_out = True

    def reset_latch(self) -> None:
        """Clear emergency latch and reset timer."""
        self.is_latched = False
        self.is_timed_out = False
        self.last_heartbeat_time = time.time()

    def get_elapsed_time(self) -> float:
        """Get seconds since last valid command heartbeat."""
        return time.time() - self.last_heartbeat_time
