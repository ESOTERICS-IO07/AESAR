/**
 * ARACHNID Rover Shared Types
 * Strictly derived from B1 Configuration Contracts & B2 Schemas
 */

export type SensorStatus =
  | 'OK'
  | 'TIMEOUT'
  | 'OUT_OF_RANGE'
  | 'DISCONNECTED'
  | 'INVALID';

export type RoverMode = 'MANUAL' | 'AUTONOMOUS';

export type CommandSource = 'MANUAL' | 'AUTONOMY' | 'SYSTEM';

export type RoverState =
  | 'DISCONNECTED'
  | 'CONNECTING'
  | 'IDLE'
  | 'MANUAL'
  | 'AUTONOMOUS'
  | 'NAVIGATING'
  | 'EXPLORING'
  | 'EMERGENCY_STOP'
  | 'FAULT';

export interface SensorStatusData {
  us_fc: SensorStatus;
  us_fl: SensorStatus;
  us_fr: SensorStatus;
  us_l: SensorStatus;
  us_r: SensorStatus;
  tof_front: SensorStatus;

  us_front?: SensorStatus;
  us_45_left?: SensorStatus;
  us_45_right?: SensorStatus;
  us_left?: SensorStatus;
  us_right?: SensorStatus;
}

export interface ToFScanData {
  angle_deg: number;
  distance_mm: number;
  valid?: boolean;
}

export interface Telemetry {
  timestamp_ms: number;
  seq: number;
  us_fc_mm: number;
  us_fl_mm: number;
  us_fr_mm: number;
  us_l_mm: number;
  us_r_mm: number;
  us_front_mm?: number;
  us_45_left_mm?: number;
  us_45_right_mm?: number;
  us_left_mm?: number;
  us_right_mm?: number;
  tof_front_mm: number;
  tof_angle_deg?: number | null;
  tof_distance_mm?: number | null;
  tof_scan?: ToFScanData | null;
  sensor_status: SensorStatusData;
  environment?: EnvironmentData | null;
}

export interface RoverStatus {
  connected: boolean;
  state: RoverState;
  mode: RoverMode;
  battery_percent: number;
  pose?: Pose2D | null;
}

export interface HealthResponse {
  status: string;
  backend: boolean;
  hardware_connected?: boolean;
  ros2_connected?: boolean;
}

export interface ModeRequest {
  mode: RoverMode;
}

export interface ModeResponse {
  success: boolean;
  mode: RoverMode;
}

export interface VelocityCommand {
  command_id: string;
  timestamp_ms: number;
  linear_mps: number;
  angular_rads: number;
  source: CommandSource;
}

export type CommandRequest = VelocityCommand;

export interface CommandResponse {
  success: boolean;
  command_id: string;
  timestamp_ms?: number;
  error?: string | null;
}

export interface StopResponse {
  success: boolean;
  stopped: boolean;
}

export interface EmergencyStopResponse {
  success: boolean;
  emergency_stop: boolean;
}

export interface Point2D {
  x: number;
  y: number;
}

export interface Pose2D {
  x: number;
  y: number;
  theta: number;
}

export interface MapData {
  resolution_m_per_cell: number;
  width: number;
  height: number;
  origin: Point2D;
  data: number[];
}

export interface NavigationData {
  status: string;
  goal: Point2D | null;
  path: Point2D[];
}

export interface ExplorationData {
  status: string;
  explored_percent: number;
  frontier_count: number;
  current_goal: Point2D | null;
}

export interface LogEntry {
  timestamp_ms: number;
  level: string;
  message: string;
  module?: string;
}

export interface LogsResponse {
  logs: LogEntry[];
}

export interface WebSocketEnvelope<T = any> {
  type: string;
  timestamp_ms: number;
  seq?: number;
  data: T;
}

export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'stale' | 'error';

// ─────────────────────────────────────────────────────────────
// AESAR Agricultural Ecosystem Intelligence Types
// ─────────────────────────────────────────────────────────────
export type AgriSensorState = 'available' | 'unavailable' | 'stale' | 'invalid';

export interface EnvironmentData {
  temperature_c?: number | null;
  humidity_percent?: number | null;
  soil_moisture_raw?: number | null;
  soil_moisture_percent?: number | null;
  timestamp?: string | number | null;
  available: boolean;
  temperature_state?: AgriSensorState;
  humidity_state?: AgriSensorState;
  soil_moisture_state?: AgriSensorState;
  status?: AgriSensorState;
}

export type CameraState = 'online' | 'ready' | 'offline' | 'connecting' | 'capturing' | 'error' | 'camera_unavailable' | 'unavailable';

export interface CameraStatus {
  connected: boolean;
  state: CameraState;
  enabled: boolean;
  provider?: string;
  camera_index?: number | null;
  stream_url: string;
  snapshot_url: string;
  last_frame_timestamp_ms?: number | null;
  last_snapshot_timestamp?: number | null;
  latency_ms?: number | null;
  error?: string | null;
  last_error?: string | null;
}

export interface CameraConfigRequest {
  provider?: string;
  local_camera_index?: number;
  stream_url?: string;
  snapshot_url?: string;
  enabled?: boolean;
  timeout_seconds?: number;
  analysis_interval_seconds?: number;
}

export type CanopyView = 'lower' | 'middle' | 'upper';
export type VisionStatus =
  | 'success'
  | 'no_detections'
  | 'image_unavailable'
  | 'image_invalid'
  | 'model_not_configured'
  | 'model_unavailable'
  | 'inference_failure';

export interface VisionDetection {
  class: string;
  category: 'pest' | 'defender';
  confidence: number;
  count: number;
}

export interface PestItem {
  name: string;
  count: number;
  confidence: number;
}

export interface DefenderItem {
  name: string;
  count: number;
  confidence: number;
}

export type PlantHealth = 'healthy' | 'mild_stress' | 'moderate_stress' | 'severe_stress' | 'unknown';
export type ImageQuality = 'EXCELLENT' | 'GOOD' | 'FAIR' | 'POOR';

export interface VisionResult {
  station_id?: number | null;
  view?: CanopyView | null;
  detections: VisionDetection[];
  status?: VisionStatus;
  error_message?: string | null;
  model_name?: string | null;
  pests?: PestItem[];
  defenders?: DefenderItem[];
  plant_health?: PlantHealth;
  leaf_damage_symptoms?: string[];
  image_quality?: ImageQuality;
  overall_confidence?: number;
  observation_notes?: string;
  notes?: string;
  provider?: string;
  timestamp_iso?: string;
}

export type VisionAnalysisResult = VisionResult;

export type EcosystemState = 'balanced' | 'moderate' | 'imbalanced' | 'unknown';

export interface AbioticRiskBreakdown {
  temperature_risk?: number | null;
  humidity_risk?: number | null;
  soil_moisture_risk?: number | null;
  overall_score?: number | null;
  combined_abiotic_risk?: number | null;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'UNKNOWN';
  primary_stressors: string[];
  notes?: string[];
}

export interface AESAStationAnalysis {
  station_id?: number | null;
  timestamp?: string | null;
  weighted_pests: number;
  weighted_defenders: number;
  pdr: number;
  abiotic_risk?: AbioticRiskBreakdown | null;
  abiotic_breakdown?: AbioticRiskBreakdown | null;
  ecosystem_state: EcosystemState;
  recommendation: string;
  confidence: number;
  data_quality: string;
  contextual_notes?: string[];
  prototype_disclaimer?: string;
}

export interface FieldAssessment {
  mission_id: string;
  mission_name?: string;
  total_stations_scouted: number;
  stations_completed?: number;
  stations_failed?: number;
  total_stations?: number;
  balanced_stations_count: number;
  moderate_stations_count: number;
  imbalanced_stations_count: number;
  unknown_stations_count: number;
  average_pdr: number;
  overall_PDR?: number;
  average_temperature_c?: number | null;
  average_temperature?: number | null;
  average_humidity_percent?: number | null;
  average_humidity?: number | null;
  average_soil_moisture_percent?: number | null;
  average_soil_moisture?: number | null;
  aggregate_pest_counts?: Record<string, number>;
  aggregate_defender_counts?: Record<string, number>;
  overall_abiotic_risk?: number | null;
  overall_ecosystem_state?: EcosystemState;
  overall_field_state?: EcosystemState;
  field_recommendation: string;
  recommendations?: string[];
  hotspot_stations: number[];
  confidence?: number;
  data_quality?: string;
  timestamp_iso?: string;
  prototype_disclaimer?: string;
}

export type MissionState =
  | 'IDLE'
  | 'INITIALIZING'
  | 'NAVIGATING'
  | 'ARRIVED_AT_STATION'
  | 'STABILIZING'
  | 'CAPTURING_IMAGE'
  | 'READING_SENSORS'
  | 'ANALYZING_IMAGE'
  | 'FUSING_DATA'
  | 'STORING_RESULT'
  | 'MOVING_TO_NEXT_STATION'
  | 'FINALIZING'
  | 'COMPLETED'
  | 'ERROR'
  | 'ABORTED';

export interface SamplingStation {
  id: number;
  x: number;
  y: number;
  name?: string | null;
  status?: string;
}

export interface StationObservationRecord {
  station?: SamplingStation | null;
  mission_id?: string | null;
  station_id?: number | null;
  timestamp?: any;
  x?: number | null;
  y?: number | null;
  temperature?: number | null;
  humidity?: number | null;
  soil_moisture?: number | null;
  environment?: EnvironmentData | null;
  image_path?: string | null;
  pest_detections?: PestItem[];
  defender_detections?: DefenderItem[];
  vision?: VisionAnalysisResult | null;
  plant_health?: any;
  pdr?: number | null;
  abiotic_risk?: number | null;
  ecosystem_state?: string | null;
  analysis?: AESAStationAnalysis | null;
  recommendation?: string | null;
  confidence?: number | null;
  data_quality?: string;
}

export interface MissionStatusResponse {
  mission_id?: string | null;
  mission_name?: string | null;
  state: MissionState;
  current_station?: SamplingStation | null;
  current_station_index: number;
  total_stations: number;
  completed_stations: number;
  remaining_stations: number;
  observations?: StationObservationRecord[];
  field_assessment?: FieldAssessment | null;
  start_time?: number | null;
  end_time?: number | null;
  message?: string;
  error_message?: string | null;
}

export type AesarMode = 'LIVE' | 'DEMO';

