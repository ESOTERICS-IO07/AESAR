"""ARACHNID Sensor Interface Serial Parser & Validators.

Adheres strictly to ARACHNID Software Integration Contract v1.0.0.
"""

from typing import Any, Dict, Optional
import json
import time


class SerialParser:
    """Parses incoming JSON lines from serial interface."""

    @staticmethod
    def parse_line(line: str) -> Optional[Dict[str, Any]]:
        """Safely parse a raw string line as JSON."""
        if not line:
            return None
        try:
            cleaned = line.strip()
            if not cleaned:
                return None
            return json.loads(cleaned)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return None


class RangePacketValidator:
    """Validates RangePacket schema according to Contract v1.0.0."""

    REQUIRED_FIELDS = [
        "timestamp_ms",
        "seq",
        "us_fc_mm",
        "us_fl_mm",
        "us_fr_mm",
        "us_l_mm",
        "us_r_mm",
        "tof_front_mm",
        "sensor_status",
    ]

    @classmethod
    def validate(cls, packet: Any) -> bool:
        if not isinstance(packet, dict):
            return False
        for field in cls.REQUIRED_FIELDS:
            if field not in packet:
                return False
        if not isinstance(packet["sensor_status"], dict):
            return False
        return True

    @classmethod
    def build_packet(
        cls,
        seq: int,
        us_fc_mm: float,
        us_fl_mm: float,
        us_fr_mm: float,
        us_l_mm: float,
        us_r_mm: float,
        tof_front_mm: float,
        sensor_status: Optional[Dict[str, str]] = None,
        timestamp_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Helper to construct a valid RangePacket."""
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)
        if sensor_status is None:
            sensor_status = {
                "us_fc": "OK",
                "us_fl": "OK",
                "us_fr": "OK",
                "us_l": "OK",
                "us_r": "OK",
                "tof_front": "OK",
            }
        return {
            "timestamp_ms": int(timestamp_ms),
            "seq": int(seq),
            "us_fc_mm": round(float(us_fc_mm), 1),
            "us_fl_mm": round(float(us_fl_mm), 1),
            "us_fr_mm": round(float(us_fr_mm), 1),
            "us_l_mm": round(float(us_l_mm), 1),
            "us_r_mm": round(float(us_r_mm), 1),
            "tof_front_mm": round(float(tof_front_mm), 1),
            "sensor_status": sensor_status,
        }


class ImuPacketValidator:
    """Validates ImuPacket schema according to Contract v1.0.0."""

    REQUIRED_FIELDS = [
        "timestamp_ms",
        "seq",
        "accel_x_mps2",
        "accel_y_mps2",
        "accel_z_mps2",
        "gyro_x_rads",
        "gyro_y_rads",
        "gyro_z_rads",
    ]

    @classmethod
    def validate(cls, packet: Any) -> bool:
        if not isinstance(packet, dict):
            return False
        for field in cls.REQUIRED_FIELDS:
            if field not in packet:
                return False
        return True

    @classmethod
    def build_packet(
        cls,
        seq: int,
        accel_x_mps2: float,
        accel_y_mps2: float,
        accel_z_mps2: float,
        gyro_x_rads: float,
        gyro_y_rads: float,
        gyro_z_rads: float,
        timestamp_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Helper to construct a valid ImuPacket."""
        if timestamp_ms is None:
            timestamp_ms = int(time.time() * 1000)
        return {
            "timestamp_ms": int(timestamp_ms),
            "seq": int(seq),
            "accel_x_mps2": round(float(accel_x_mps2), 4),
            "accel_y_mps2": round(float(accel_y_mps2), 4),
            "accel_z_mps2": round(float(accel_z_mps2), 4),
            "gyro_x_rads": round(float(gyro_x_rads), 4),
            "gyro_y_rads": round(float(gyro_y_rads), 4),
            "gyro_z_rads": round(float(gyro_z_rads), 4),
        }