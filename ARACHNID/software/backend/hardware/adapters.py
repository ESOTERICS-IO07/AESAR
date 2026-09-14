from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from datetime import datetime, timezone

from backend.models.schemas import (
    AgriSensorState,
    EnvironmentData,
    ExplorationData,
    MapData,
    NavigationData,
    Point2D,
    SensorStatus,
    SensorStatusData,
    Telemetry,
    ToFScanData,
)
from backend.hardware.calibration import SoilMoistureCalibrator
from backend.config.settings import settings


# Hardware Range Limits (mm)
MAX_ULTRASONIC_RANGE_MM = 4000.0
MIN_ULTRASONIC_RANGE_MM = 20.0
MAX_TOF_RANGE_MM = 2000.0
MIN_TOF_RANGE_MM = 10.0


class SensorAdapter:
    """
    Adapter and validator for ARACHNID 5x Ultrasonic + 1x Scanning ToF distance sensors.
    """

    @staticmethod
    def validate_sensor_reading(
        val_mm: Optional[float],
        min_range_mm: float,
        max_range_mm: float,
    ) -> tuple[float, SensorStatus]:
        if val_mm is None or val_mm < 0:
            return -1.0, SensorStatus.DISCONNECTED

        # 999 sentinel from ESP32 firmware represents disconnected or no-echo
        if val_mm >= 999.0 and val_mm <= 999.5:
            return -1.0, SensorStatus.TIMEOUT

        if val_mm < min_range_mm or val_mm > max_range_mm:
            return float(val_mm), SensorStatus.OUT_OF_RANGE

        return float(val_mm), SensorStatus.OK

    @classmethod
    def convert_raw_telemetry(
        cls,
        raw: Dict[str, Any],
        seq: int,
    ) -> Telemetry:
        now_ms = int(time.time() * 1000)
        u_dict = raw.get("ultrasonic", {}) if isinstance(raw.get("ultrasonic"), dict) else {}

        # 0. Ultrasonic Front (us_front / us_fc)
        us_fc_raw = raw.get("us_front_mm", raw.get("us_front", u_dict.get("front_mm", raw.get("us_fc_mm", raw.get("us_fc", -1.0)))))
        us_fc_mm, us_fc_status = cls.validate_sensor_reading(
            us_fc_raw, MIN_ULTRASONIC_RANGE_MM, MAX_ULTRASONIC_RANGE_MM
        )

        # 1. Ultrasonic 45-Left (us_45_left / us_fl)
        us_fl_raw = raw.get("us_45_left_mm", raw.get("us_45_left", u_dict.get("front_left_45_mm", raw.get("us_fl_mm", raw.get("us_fl", -1.0)))))
        us_fl_mm, us_fl_status = cls.validate_sensor_reading(
            us_fl_raw, MIN_ULTRASONIC_RANGE_MM, MAX_ULTRASONIC_RANGE_MM
        )

        # 2. Ultrasonic 45-Right (us_45_right / us_fr)
        us_fr_raw = raw.get("us_45_right_mm", raw.get("us_45_right", u_dict.get("front_right_45_mm", raw.get("us_fr_mm", raw.get("us_fr", -1.0)))))
        us_fr_mm, us_fr_status = cls.validate_sensor_reading(
            us_fr_raw, MIN_ULTRASONIC_RANGE_MM, MAX_ULTRASONIC_RANGE_MM
        )

        # 3. Ultrasonic Left (us_left / us_l)
        us_l_raw = raw.get("us_left_mm", raw.get("us_left", u_dict.get("left_mm", raw.get("us_l_mm", raw.get("us_l", -1.0)))))
        us_l_mm, us_l_status = cls.validate_sensor_reading(
            us_l_raw, MIN_ULTRASONIC_RANGE_MM, MAX_ULTRASONIC_RANGE_MM
        )

        # 4. Ultrasonic Right (us_right / us_r)
        us_r_raw = raw.get("us_right_mm", raw.get("us_right", u_dict.get("right_mm", raw.get("us_r_mm", raw.get("us_r", -1.0)))))
        us_r_mm, us_r_status = cls.validate_sensor_reading(
            us_r_raw, MIN_ULTRASONIC_RANGE_MM, MAX_ULTRASONIC_RANGE_MM
        )

        # 5. Time-of-Flight Front
        tof_dict = raw.get("tof_scan", {}) if isinstance(raw.get("tof_scan"), dict) else {}
        tof_raw = raw.get("tof_front_mm", raw.get("tof_front", tof_dict.get("distance_mm", raw.get("tof_distance_mm", raw.get("tof", -1.0)))))
        # If centimeters transmitted, convert to mm
        if "distance_cm" in tof_dict:
            tof_raw = float(tof_dict["distance_cm"]) * 10.0
        elif "tof_distance_cm" in raw:
            tof_raw = float(raw["tof_distance_cm"]) * 10.0

        tof_mm, tof_status = cls.validate_sensor_reading(
            tof_raw, MIN_TOF_RANGE_MM, MAX_TOF_RANGE_MM
        )

        # 6. Scanning ToF Angle and Distance
        tof_angle: Optional[float] = None
        if "tof_angle_deg" in raw:
            tof_angle = float(raw["tof_angle_deg"])
        elif "angle_deg" in tof_dict:
            tof_angle = float(tof_dict["angle_deg"])

        tof_scan_obj = None
        if tof_angle is not None:
            is_valid = (tof_mm >= MIN_TOF_RANGE_MM and tof_mm <= MAX_TOF_RANGE_MM and tof_status == SensorStatus.OK)
            tof_scan_obj = ToFScanData(
                angle_deg=tof_angle,
                distance_mm=tof_mm,
                valid=is_valid,
            )

        return Telemetry(
            timestamp_ms=raw.get("timestamp_ms", now_ms),
            seq=seq,
            us_fc_mm=us_fc_mm,
            us_fl_mm=us_fl_mm,
            us_fr_mm=us_fr_mm,
            us_l_mm=us_l_mm,
            us_r_mm=us_r_mm,
            us_front_mm=us_fc_mm,
            us_45_left_mm=us_fl_mm,
            us_45_right_mm=us_fr_mm,
            us_left_mm=us_l_mm,
            us_right_mm=us_r_mm,
            tof_front_mm=tof_mm,
            tof_angle_deg=tof_angle,
            tof_distance_mm=tof_mm if tof_angle is not None else None,
            tof_scan=tof_scan_obj,
            sensor_status=SensorStatusData(
                us_fc=us_fc_status,
                us_fl=us_fl_status,
                us_fr=us_fr_status,
                us_l=us_l_status,
                us_r=us_r_status,
                us_front=us_fc_status,
                us_45_left=us_fl_status,
                us_45_right=us_fr_status,
                us_left=us_l_status,
                us_right=us_r_status,
                tof_front=tof_status,
            ),
            environment=EnvironmentalAdapter.convert_environmental_data(raw, now_ms),
        )


class EnvironmentalAdapter:
    """
    Adapter and validator for AESAR DHT22 and Soil Moisture sensors.
    Applies configurable soil moisture calibration and range validation.
    Guaranteed never to raise unhandled exceptions or crash telemetry processing.
    """

    _calibrator: Optional[SoilMoistureCalibrator] = None

    @classmethod
    def get_calibrator(cls) -> SoilMoistureCalibrator:
        if cls._calibrator is None:
            soil_cfg = settings.environmental_config.get("soil_moisture", {})
            cls._calibrator = SoilMoistureCalibrator(
                raw_dry=soil_cfg.get("raw_dry", 3200.0),
                raw_wet=soil_cfg.get("raw_wet", 1400.0),
                invert=soil_cfg.get("invert", True),
                min_valid_raw=soil_cfg.get("min_valid_raw", 100.0),
                max_valid_raw=soil_cfg.get("max_valid_raw", 4095.0),
            )
        return cls._calibrator

    @classmethod
    def convert_environmental_data(cls, raw: Dict[str, Any], now_ms: int) -> EnvironmentData:
        try:
            env_dict = raw.get("environment", {}) if isinstance(raw.get("environment"), dict) else {}

            dht_cfg = settings.environmental_config.get("dht22", {})
            temp_min = float(dht_cfg.get("temp_min_c", -40.0))
            temp_max = float(dht_cfg.get("temp_max_c", 80.0))
            hum_min = float(dht_cfg.get("humidity_min_pct", 0.0))
            hum_max = float(dht_cfg.get("humidity_max_pct", 100.0))

            # 1. Temperature
            temp_raw = env_dict.get("temperature_c", raw.get("temp_c", raw.get("temperature_c")))
            temp_c: Optional[float] = None
            temp_state = AgriSensorState.UNAVAILABLE

            if temp_raw is not None:
                try:
                    t_val = float(temp_raw)
                    if t_val <= -990.0:  # ESP32 sentinel for disconnected
                        temp_state = AgriSensorState.UNAVAILABLE
                    elif t_val < temp_min or t_val > temp_max:
                        temp_state = AgriSensorState.INVALID
                    else:
                        temp_c = round(t_val, 1)
                        temp_state = AgriSensorState.AVAILABLE
                except (ValueError, TypeError):
                    temp_state = AgriSensorState.INVALID

            # 2. Humidity
            hum_raw = env_dict.get("humidity_percent", raw.get("humidity_pct", raw.get("humidity_percent")))
            hum_pct: Optional[float] = None
            hum_state = AgriSensorState.UNAVAILABLE

            if hum_raw is not None:
                try:
                    h_val = float(hum_raw)
                    if h_val <= -990.0:
                        hum_state = AgriSensorState.UNAVAILABLE
                    elif h_val < hum_min or h_val > hum_max:
                        hum_state = AgriSensorState.INVALID
                    else:
                        hum_pct = round(h_val, 1)
                        hum_state = AgriSensorState.AVAILABLE
                except (ValueError, TypeError):
                    hum_state = AgriSensorState.INVALID

            # 3. Soil Moisture
            calibrator = cls.get_calibrator()
            soil_raw_val = env_dict.get("soil_moisture_raw", raw.get("soil_moisture_raw", raw.get("soil_raw")))
            soil_pct_direct = env_dict.get("soil_moisture_percent", raw.get("soil_moisture_pct"))

            soil_raw: Optional[float] = None
            soil_pct: Optional[float] = None
            soil_state = AgriSensorState.UNAVAILABLE

            if soil_raw_val is not None:
                try:
                    s_raw = float(soil_raw_val)
                    if s_raw <= -990.0:
                        soil_state = AgriSensorState.UNAVAILABLE
                    elif not calibrator.is_raw_valid(s_raw):
                        soil_state = AgriSensorState.INVALID
                    else:
                        soil_raw = round(s_raw, 1)
                        soil_pct = calibrator.raw_to_percent(s_raw)
                        soil_state = AgriSensorState.AVAILABLE
                except (ValueError, TypeError):
                    soil_state = AgriSensorState.INVALID
            elif soil_pct_direct is not None:
                try:
                    sp_val = float(soil_pct_direct)
                    if sp_val < 0.0 or sp_val > 100.0:
                        soil_state = AgriSensorState.INVALID
                    else:
                        soil_pct = round(sp_val, 1)
                        soil_state = AgriSensorState.AVAILABLE
                except (ValueError, TypeError):
                    soil_state = AgriSensorState.INVALID

            # Determine overall availability and status
            available = (
                temp_state == AgriSensorState.AVAILABLE
                or hum_state == AgriSensorState.AVAILABLE
                or soil_state == AgriSensorState.AVAILABLE
            )

            if available:
                status = AgriSensorState.AVAILABLE
            elif (
                temp_state == AgriSensorState.INVALID
                or hum_state == AgriSensorState.INVALID
                or soil_state == AgriSensorState.INVALID
            ):
                status = AgriSensorState.INVALID
            else:
                status = AgriSensorState.UNAVAILABLE

            ts_str = env_dict.get("timestamp") or datetime.now(timezone.utc).isoformat()

            return EnvironmentData(
                temperature_c=temp_c,
                humidity_percent=hum_pct,
                soil_moisture_raw=soil_raw,
                soil_moisture_percent=soil_pct,
                timestamp=ts_str,
                timestamp_ms=now_ms,
                available=available,
                temperature_state=temp_state,
                humidity_state=hum_state,
                soil_moisture_state=soil_state,
                status=status,
            )
        except Exception:
            return EnvironmentData(
                timestamp=datetime.now(timezone.utc).isoformat(),
                timestamp_ms=now_ms,
                available=False,
                status=AgriSensorState.UNAVAILABLE,
            )

    @classmethod
    def convert_raw_environment(cls, raw: Dict[str, Any], now_ms: int = 0) -> EnvironmentData:
        return cls.convert_environmental_data(raw, now_ms)



class MapAdapter:
    """
    Adapter converting JSON OccupancyGrid into ARACHNID MapData.
    """

    @staticmethod
    def convert_occupancy_grid(raw_map: Dict[str, Any]) -> MapData:
        info = raw_map.get("info", {})
        origin = info.get("origin", raw_map.get("origin", {}))
        pos = origin.get("position", origin)

        return MapData(
            resolution_m_per_cell=float(info.get("resolution", raw_map.get("resolution_m_per_cell", 0.05))),
            width=int(info.get("width", raw_map.get("width", 20))),
            height=int(info.get("height", raw_map.get("height", 20))),
            origin=Point2D(
                x=float(pos.get("x", 0.0)),
                y=float(pos.get("y", 0.0)),
            ),
            data=list(raw_map.get("data", [0] * (20 * 20))),
        )


class NavigationAdapter:
    """
    Adapter converting JSON Path and Navigation Action status into NavigationData.
    """

    @staticmethod
    def convert_navigation_data(raw_nav: Dict[str, Any]) -> NavigationData:
        goal_raw = raw_nav.get("goal")
        goal = None
        if goal_raw:
            goal = Point2D(x=float(goal_raw.get("x", 0.0)), y=float(goal_raw.get("y", 0.0)))

        path_raw = raw_nav.get("path", [])
        path: List[Point2D] = []
        for pt in path_raw:
            if isinstance(pt, dict):
                path.append(Point2D(x=float(pt.get("x", 0.0)), y=float(pt.get("y", 0.0))))
            elif hasattr(pt, "x") and hasattr(pt, "y"):
                path.append(Point2D(x=float(pt.x), y=float(pt.y)))

        return NavigationData(
            status=str(raw_nav.get("status", "IDLE")),
            goal=goal,
            path=path,
        )


class ExplorationAdapter:
    """
    Adapter converting JSON Frontier Exploration topics into ExplorationData.
    """

    @staticmethod
    def convert_exploration_data(raw_exp: Dict[str, Any]) -> ExplorationData:
        goal_raw = raw_exp.get("current_goal")
        goal = None
        if goal_raw:
            goal = Point2D(x=float(goal_raw.get("x", 0.0)), y=float(goal_raw.get("y", 0.0)))

        return ExplorationData(
            status=str(raw_exp.get("status", "IDLE")),
            explored_percent=float(raw_exp.get("explored_percent", 0.0)),
            frontier_count=int(raw_exp.get("frontier_count", 0)),
            current_goal=goal,
        )



