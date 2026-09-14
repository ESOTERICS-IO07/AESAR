"""ARACHNID Sensor Filtering Utilities.

Provides Median filtering for ultrasonics, Moving Average for ToF,
and Low-Pass filtering for IMU data.
"""

from collections import deque
from typing import Optional, Union
import numpy as np


class MedianFilter:
    """Median filter for ultrasonic range sensors."""

    def __init__(self, window_size: int = 5):
        if window_size < 1:
            window_size = 1
        self.window_size = window_size
        self.values: deque[float] = deque(maxlen=window_size)

    def update(self, value: Union[int, float]) -> float:
        v = float(value)
        if v > 0.0:
            self.values.append(v)
        if not self.values:
            return 2000.0
        return float(np.median(self.values))

    def reset(self) -> None:
        self.values.clear()


class MovingAverageFilter:
    """Moving average filter for Time-of-Flight range sensor."""

    def __init__(self, window_size: int = 5):
        if window_size < 1:
            window_size = 1
        self.window_size = window_size
        self.values: deque[float] = deque(maxlen=window_size)

    def update(self, value: Union[int, float]) -> float:
        v = float(value)
        if v > 0.0:
            self.values.append(v)
        if not self.values:
            return 2000.0
        return float(np.mean(self.values))

    def reset(self) -> None:
        self.values.clear()


class LowPassFilter:
    """First-order infinite impulse response (IIR) low-pass filter for IMU data."""

    def __init__(self, alpha: float = 0.25):
        # alpha is smoothing factor between 0.0 and 1.0
        self.alpha = max(0.0, min(1.0, float(alpha)))
        self.previous: Optional[float] = None

    def update(self, value: Union[int, float]) -> float:
        val = float(value)
        if self.previous is None:
            self.previous = val
            return val

        filtered = self.alpha * val + (1.0 - self.alpha) * self.previous
        self.previous = filtered
        return filtered

    def reset(self) -> None:
        self.previous = None