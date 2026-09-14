from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("aesar.calibration")


class SoilMoistureCalibrator:
    """
    Calibrates raw analog ADC sensor values into volumetric soil moisture percentage (0.0% to 100.0%).

    Supports configurable dry/wet reference points and polarity inversion.
    Standard capacitive soil sensors (e.g. v1.2) output higher voltage (higher ADC)
    in dry air and lower voltage in water (invert = True).
    """

    def __init__(
        self,
        raw_dry: float = 3200.0,
        raw_wet: float = 1400.0,
        invert: bool = True,
        min_valid_raw: float = 100.0,
        max_valid_raw: float = 4095.0,
        dry_adc: Optional[float] = None,
        wet_adc: Optional[float] = None,
    ) -> None:
        self.raw_dry = float(dry_adc if dry_adc is not None else raw_dry)
        self.raw_wet = float(wet_adc if wet_adc is not None else raw_wet)
        self.invert = bool(invert)
        self.min_valid_raw = float(min_valid_raw)
        self.max_valid_raw = float(max_valid_raw)

    def is_raw_valid(self, raw_val: Optional[float]) -> bool:
        if raw_val is None:
            return False
        # Disallow sentinels (e.g. -1 or negative) or disconnected rails
        if raw_val < self.min_valid_raw or raw_val > self.max_valid_raw:
            return False
        return True

    def raw_to_percent(self, raw_val: Optional[float]) -> Optional[float]:
        """
        Converts raw ADC to a normalized percentage between 0.0% and 100.0%.
        Returns None if raw_val is invalid or out of physical bounds.
        """
        if not self.is_raw_valid(raw_val):
            return None

        # Guard against zero-division if raw_dry == raw_wet
        denominator = self.raw_dry - self.raw_wet if self.invert else self.raw_wet - self.raw_dry
        if abs(denominator) < 1e-6:
            logger.warning("Soil moisture calibration denominator is near zero. Returning 50.0%")
            return 50.0

        if self.invert:
            # raw_dry -> 0%, raw_wet -> 100%
            pct = ((self.raw_dry - raw_val) / (self.raw_dry - self.raw_wet)) * 100.0
        else:
            # raw_dry -> 0%, raw_wet -> 100%
            pct = ((raw_val - self.raw_dry) / (self.raw_wet - self.raw_dry)) * 100.0

        # Clamp between 0.0 and 100.0
        clamped = max(0.0, min(100.0, pct))
        return round(clamped, 1)

    def calibrate(self, raw_val: Optional[float]) -> tuple[Optional[float], bool]:
        """Returns tuple of (percentage, is_valid)."""
        valid = self.is_raw_valid(raw_val)
        pct = self.raw_to_percent(raw_val) if valid else None
        return pct, valid
