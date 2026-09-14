from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class SensorStatus(str, Enum):
    OK = "OK"
    TIMEOUT = "TIMEOUT"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    DISCONNECTED = "DISCONNECTED"
    INVALID = "INVALID"


class RoverMode(str, Enum):
    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"


class CommandSource(str, Enum):
    MANUAL = "MANUAL"
    AUTONOMY = "AUTONOMY"
    SYSTEM = "SYSTEM"


class RoverState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    IDLE = "IDLE"
    MANUAL = "MANUAL"
    AUTONOMOUS = "AUTONOMOUS"
    NAVIGATING = "NAVIGATING"
    EXPLORING = "EXPLORING"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    FAULT = "FAULT"


class HealthResponse(BaseModel):
    status: str = "ok"
    backend: bool = True
    hardware_connected: bool = True


class ToFScanData(BaseModel):
    angle_deg: float = 0.0
    distance_mm: float = -1.0
    valid: bool = False


class SensorStatusData(BaseModel):
    us_fc: SensorStatus = SensorStatus.OK
    us_fl: SensorStatus = SensorStatus.OK
    us_fr: SensorStatus = SensorStatus.OK
    us_l: SensorStatus = SensorStatus.OK
    us_r: SensorStatus = SensorStatus.OK
    tof_front: SensorStatus = SensorStatus.OK

    us_front: Optional[SensorStatus] = None
    us_45_left: Optional[SensorStatus] = None
    us_45_right: Optional[SensorStatus] = None
    us_left: Optional[SensorStatus] = None
    us_right: Optional[SensorStatus] = None


class AgriSensorState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    STALE = "stale"
    INVALID = "invalid"


class EnvironmentData(BaseModel):
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = None
    soil_moisture_raw: Optional[float] = None
    soil_moisture_percent: Optional[float] = None
    timestamp: Optional[str] = None
    timestamp_ms: Optional[int] = None
    available: bool = False
    temperature_state: AgriSensorState = AgriSensorState.UNAVAILABLE
    humidity_state: AgriSensorState = AgriSensorState.UNAVAILABLE
    soil_moisture_state: AgriSensorState = AgriSensorState.UNAVAILABLE
    status: AgriSensorState = AgriSensorState.UNAVAILABLE


class Telemetry(BaseModel):
    timestamp_ms: int = 0
    seq: int = 0

    # Person A aliases
    us_fc_mm: float = -1.0
    us_fl_mm: float = -1.0
    us_fr_mm: float = -1.0
    us_l_mm: float = -1.0
    us_r_mm: float = -1.0

    # Physical hardware named channels
    us_front_mm: float = -1.0
    us_right_mm: float = -1.0
    us_left_mm: float = -1.0
    us_45_right_mm: float = -1.0
    us_45_left_mm: float = -1.0

    tof_front_mm: float = -1.0
    tof_angle_deg: Optional[float] = None
    tof_distance_mm: Optional[float] = None
    tof_scan: Optional[ToFScanData] = None

    sensor_status: SensorStatusData = Field(default_factory=SensorStatusData)
    environment: EnvironmentData = Field(default_factory=lambda: EnvironmentData())



class RoverStatus(BaseModel):
    connected: bool = False
    state: RoverState = RoverState.DISCONNECTED
    mode: RoverMode = RoverMode.MANUAL
    battery_percent: float = Field(default=-1.0, ge=-1.0, le=100.0)
    pose: Optional[Pose2D] = None


class ModeRequest(BaseModel):
    mode: RoverMode


class ModeResponse(BaseModel):
    success: bool = True
    mode: RoverMode


class VelocityCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    command_id: str = Field(..., min_length=1)
    timestamp_ms: int = Field(...)
    linear_mps: float = Field(...)
    angular_rads: float = Field(...)
    source: CommandSource = Field(default=CommandSource.MANUAL)

    @field_validator("linear_mps", "angular_rads")
    @classmethod
    def check_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Velocity components must be finite numeric values")
        return v

    @field_validator("timestamp_ms")
    @classmethod
    def check_positive_timestamp(cls, v: int) -> int:
        if v < 0:
            raise ValueError("timestamp_ms cannot be negative")
        return v


# Alias CommandRequest to VelocityCommand for API compatibility
CommandRequest = VelocityCommand


class CommandResponse(BaseModel):
    success: bool = True
    command_id: str


class StopResponse(BaseModel):
    success: bool = True
    stopped: bool = True


class EmergencyStopResponse(BaseModel):
    success: bool = True
    emergency_stop: bool = True


class Point2D(BaseModel):
    x: float = 0.0
    y: float = 0.0


class Pose2D(BaseModel):
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class MapData(BaseModel):
    resolution_m_per_cell: float = 0.05
    width: int = 0
    height: int = 0
    origin: Point2D = Field(default_factory=Point2D)
    data: List[int] = Field(default_factory=list)


class NavigationData(BaseModel):
    status: str = "IDLE"
    goal: Optional[Point2D] = None
    path: List[Point2D] = Field(default_factory=list)


class ExplorationData(BaseModel):
    status: str = "IDLE"
    explored_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    frontier_count: int = Field(default=0, ge=0)
    current_goal: Optional[Point2D] = None


class LogEntry(BaseModel):
    timestamp_ms: int
    level: str
    message: str


class LogsResponse(BaseModel):
    logs: List[LogEntry] = Field(default_factory=list)


class WebSocketMessage(BaseModel):
    type: str
    timestamp_ms: int
    data: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────
# AESAR Camera Schemas
# ─────────────────────────────────────────────────────────────
class CameraState(str, Enum):
    ONLINE = "online"
    READY = "ready"
    OFFLINE = "offline"
    CONNECTING = "connecting"
    CAPTURING = "capturing"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    CAMERA_UNAVAILABLE = "camera_unavailable"


class CameraStatus(BaseModel):
    connected: bool = False
    state: CameraState = CameraState.OFFLINE
    enabled: bool = True
    provider: Optional[str] = "local"
    camera_index: Optional[int] = 0
    stream_url: str = ""
    snapshot_url: str = ""
    last_frame_timestamp_ms: Optional[int] = None
    last_snapshot_timestamp: Optional[float] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    last_error: Optional[str] = None


class CameraConfigRequest(BaseModel):
    provider: Optional[str] = None
    local_camera_index: Optional[int] = None
    stream_url: Optional[str] = None
    snapshot_url: Optional[str] = None
    enabled: Optional[bool] = True
    timeout_seconds: Optional[float] = 3.0
    analysis_interval_seconds: Optional[int] = 0


# ─────────────────────────────────────────────────────────────
# AESAR Vision Schemas
# ─────────────────────────────────────────────────────────────
class CanopyView(str, Enum):
    LOWER = "lower"
    MIDDLE = "middle"
    UPPER = "upper"


class VisionStatus(str, Enum):
    SUCCESS = "success"
    NO_DETECTIONS = "no_detections"
    IMAGE_UNAVAILABLE = "image_unavailable"
    IMAGE_INVALID = "image_invalid"
    MODEL_NOT_CONFIGURED = "model_not_configured"
    MODEL_UNAVAILABLE = "model_unavailable"
    INFERENCE_FAILURE = "inference_failure"


class PestItem(BaseModel):
    name: str
    count: int = Field(default=0, ge=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DefenderItem(BaseModel):
    name: str
    count: int = Field(default=0, ge=0)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ImageQuality(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"


class PlantHealth(str, Enum):
    HEALTHY = "healthy"
    MILD_STRESS = "mild_stress"
    MODERATE_STRESS = "moderate_stress"
    SEVERE_STRESS = "severe_stress"
    UNKNOWN = "unknown"


class VisionDetection(BaseModel):
    """
    Contract Vision Detection item.
    Follows schema: { "class": str, "category": "pest" | "defender", "confidence": float, "count": int }
    """
    model_config = ConfigDict(populate_by_name=True)

    class_name: str = Field(alias="class")
    category: Literal["pest", "defender"]
    confidence: float = Field(ge=0.0, le=1.0)
    count: int = Field(ge=0)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in ("pest", "defender"):
            raise ValueError("Category must be either 'pest' or 'defender'")
        return v


class VisionResult(BaseModel):
    """
    Contract Vision Result structure:
    {
      "station_id": 3,
      "view": "upper",
      "detections": [ ... ]
    }
    """
    model_config = ConfigDict(populate_by_name=True)

    station_id: Optional[int] = None
    view: Optional[Literal["lower", "middle", "upper"]] = None
    detections: List[VisionDetection] = Field(default_factory=list)
    status: VisionStatus = VisionStatus.SUCCESS
    error_message: Optional[str] = None
    model_name: Optional[str] = None
    image_metadata: Optional[Dict[str, Any]] = None
    image_quality: Optional[ImageQuality] = ImageQuality.GOOD
    plant_health: Optional[PlantHealth] = PlantHealth.HEALTHY
    leaf_damage_symptoms: List[str] = Field(default_factory=list)
    observation_notes: str = ""
    notes: str = ""
    provider: str = "mock"
    timestamp_iso: str = ""

    def __init__(self, **data: Any) -> None:
        # Support initializing with legacy pests/defenders directly if detections omitted
        if "detections" not in data and ("pests" in data or "defenders" in data):
            dets: List[VisionDetection] = []
            for p in data.get("pests", []):
                name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else str(p))
                cnt = getattr(p, "count", 1) if not isinstance(p, dict) else p.get("count", 1)
                conf = getattr(p, "confidence", 0.9) if not isinstance(p, dict) else p.get("confidence", 0.9)
                dets.append(VisionDetection(class_name=name, category="pest", count=cnt, confidence=conf))
            for d in data.get("defenders", []):
                name = getattr(d, "name", None) or (d.get("name") if isinstance(d, dict) else str(d))
                cnt = getattr(d, "count", 1) if not isinstance(d, dict) else d.get("count", 1)
                conf = getattr(d, "confidence", 0.9) if not isinstance(d, dict) else d.get("confidence", 0.9)
                dets.append(VisionDetection(class_name=name, category="defender", count=cnt, confidence=conf))
            data["detections"] = dets
        super().__init__(**data)

    @computed_field
    @property
    def pests(self) -> List[PestItem]:
        return [
            PestItem(name=d.class_name, count=d.count, confidence=d.confidence)
            for d in self.detections
            if d.category == "pest"
        ]

    @computed_field
    @property
    def defenders(self) -> List[DefenderItem]:
        return [
            DefenderItem(name=d.class_name, count=d.count, confidence=d.confidence)
            for d in self.detections
            if d.category == "defender"
        ]

    @computed_field
    @property
    def overall_confidence(self) -> float:
        if not self.detections:
            return 1.0 if self.status == VisionStatus.SUCCESS else 0.0
        total_count = sum(d.count for d in self.detections)
        if total_count == 0:
            return 0.0
        return round(sum(d.confidence * d.count for d in self.detections) / total_count, 3)


# Backward compatibility alias
VisionAnalysisResult = VisionResult


# ─────────────────────────────────────────────────────────────
# AESAR AESA Engine Schemas
# ─────────────────────────────────────────────────────────────
class EcosystemState(str, Enum):
    BALANCED = "balanced"
    MODERATE = "moderate"
    IMBALANCED = "imbalanced"
    UNKNOWN = "unknown"


class AbioticRiskBreakdown(BaseModel):
    temperature_risk: Optional[float] = None
    humidity_risk: Optional[float] = None
    soil_moisture_risk: Optional[float] = None
    overall_score: Optional[float] = 0.0
    combined_abiotic_risk: Optional[float] = None
    risk_level: str = "LOW"
    primary_stressors: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class AESAStationAnalysis(BaseModel):
    station_id: Optional[int] = None
    timestamp: Optional[str] = None
    weighted_pests: float = 0.0
    weighted_defenders: float = 0.0
    pdr: float = 0.0
    abiotic_risk: Optional[AbioticRiskBreakdown] = None
    abiotic_breakdown: Optional[AbioticRiskBreakdown] = None
    ecosystem_state: EcosystemState = EcosystemState.UNKNOWN
    recommendation: str = "Insufficient data for a reliable ecosystem assessment. Re-sample this station."
    confidence: float = 0.0
    data_quality: str = "good"
    contextual_notes: List[str] = Field(default_factory=list)
    prototype_disclaimer: str = "Prototype decision rules pending agricultural field validation."


class FieldAssessment(BaseModel):
    mission_id: str = ""
    mission_name: str = ""
    total_stations_scouted: int = 0
    stations_completed: int = 0
    stations_failed: int = 0
    total_stations: int = 0
    balanced_stations_count: int = 0
    moderate_stations_count: int = 0
    imbalanced_stations_count: int = 0
    unknown_stations_count: int = 0
    average_pdr: float = 0.0
    overall_PDR: float = 0.0
    average_temperature_c: Optional[float] = None
    average_temperature: Optional[float] = None
    average_humidity_percent: Optional[float] = None
    average_humidity: Optional[float] = None
    average_soil_moisture_percent: Optional[float] = None
    average_soil_moisture: Optional[float] = None
    aggregate_pest_counts: Dict[str, int] = Field(default_factory=dict)
    aggregate_defender_counts: Dict[str, int] = Field(default_factory=dict)
    overall_abiotic_risk: Optional[float] = None
    overall_ecosystem_state: EcosystemState = EcosystemState.UNKNOWN
    overall_field_state: Optional[EcosystemState] = None
    field_recommendation: str = ""
    recommendations: List[str] = Field(default_factory=list)
    hotspot_stations: List[int] = Field(default_factory=list)
    confidence: float = 0.0
    data_quality: str = "good"
    timestamp_iso: str = ""
    prototype_disclaimer: str = "Prototype decision rules pending agricultural field validation."


# ─────────────────────────────────────────────────────────────
# AESAR Mission Schemas
# ─────────────────────────────────────────────────────────────
class MissionState(str, Enum):
    IDLE = "IDLE"
    INITIALIZING = "INITIALIZING"
    NAVIGATING = "NAVIGATING"
    ARRIVED_AT_STATION = "ARRIVED_AT_STATION"
    STABILIZING = "STABILIZING"
    CAPTURING_IMAGE = "CAPTURING_IMAGE"
    READING_SENSORS = "READING_SENSORS"
    ANALYZING_IMAGE = "ANALYZING_IMAGE"
    FUSING_DATA = "FUSING_DATA"
    STORING_RESULT = "STORING_RESULT"
    MOVING_TO_NEXT_STATION = "MOVING_TO_NEXT_STATION"
    FINALIZING = "FINALIZING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    ABORTED = "ABORTED"


class SamplingStation(BaseModel):
    id: int
    x: float
    y: float
    name: Optional[str] = None
    status: str = "PENDING"  # "PENDING", "ACTIVE", "COMPLETED", "FAILED", "SKIPPED"


class StationObservationRecord(BaseModel):
    station: Optional[SamplingStation] = None
    mission_id: Optional[str] = None
    station_id: Optional[int] = None
    timestamp: Any = None
    x: Optional[float] = None
    y: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    environment: Optional[EnvironmentData] = None
    image_path: Optional[str] = None
    pest_detections: List[PestItem] = Field(default_factory=list)
    defender_detections: List[DefenderItem] = Field(default_factory=list)
    vision: Optional[VisionAnalysisResult] = None
    plant_health: Optional[Any] = None
    pdr: Optional[float] = None
    abiotic_risk: Optional[float] = None
    ecosystem_state: Optional[str] = None
    analysis: Optional[AESAStationAnalysis] = None
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    data_quality: Optional[str] = "good"


class MissionPlan(BaseModel):
    name: str = "Agricultural Scouting Mission"
    stations: List[SamplingStation]
    stabilize_delay_seconds: float = 1.5
    waypoint_tolerance_m: float = 0.20


class MissionStatusResponse(BaseModel):
    mission_id: Optional[str] = None
    mission_name: Optional[str] = None
    state: MissionState = MissionState.IDLE
    current_station: Optional[SamplingStation] = None
    current_station_index: int = 0
    total_stations: int = 0
    completed_stations: int = 0
    remaining_stations: int = 0
    observations: List[StationObservationRecord] = Field(default_factory=list)
    field_assessment: Optional[FieldAssessment] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    message: str = ""
    error_message: Optional[str] = None


class AesarModeRequest(BaseModel):
    mode: str = "DEMO"


class AesarModeResponse(BaseModel):
    mode: str = "DEMO"
    description: str = ""


