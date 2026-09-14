import math
import time
from typing import Tuple

class PoseEstimator:
    """
    Estimates the rover's global pose (x, y, theta) using open-loop kinematics.
    Since the physical hardware lacks wheel encoders and an IMU, this relies
    purely on integrating commanded velocities over time (dead reckoning).
    
    This WILL drift over time, but it provides a local coordinate frame
    sufficient for short-term frontier exploration.
    """
    def __init__(self) -> None:
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0  # radians (0 is pointing along +x axis)
        
        self._last_update_time = time.time()
        self._current_v = 0.0  # linear velocity (m/s)
        self._current_w = 0.0  # angular velocity (rad/s)

    def update_velocity(self, v: float, w: float) -> None:
        """Update the currently active velocity commands."""
        self._step()
        self._current_v = v
        self._current_w = w

    def get_pose(self) -> Tuple[float, float, float]:
        """Returns the current estimated pose (x, y, theta)."""
        self._step()
        return self.x, self.y, self.theta
        
    def _step(self) -> None:
        """Integrates velocity over the elapsed time since last step."""
        now = time.time()
        dt = now - self._last_update_time
        self._last_update_time = now
        
        if dt > 0 and (self._current_v != 0.0 or self._current_w != 0.0):
            # Simple kinematic model for a differential drive robot
            if abs(self._current_w) < 1e-6:
                # Moving straight
                self.x += self._current_v * math.cos(self.theta) * dt
                self.y += self._current_v * math.sin(self.theta) * dt
            else:
                # Moving in an arc
                radius = self._current_v / self._current_w
                self.x += radius * (math.sin(self.theta + self._current_w * dt) - math.sin(self.theta))
                self.y -= radius * (math.cos(self.theta + self._current_w * dt) - math.cos(self.theta))
                self.theta += self._current_w * dt
                
            # Normalize theta to [-pi, pi]
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
