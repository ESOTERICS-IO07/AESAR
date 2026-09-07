# Interfaces

This document defines stable interfaces between teammates. 

## Hardware Telemetry
Owner: Person 1 (Hardware Integration)
```json
{
  "type": "sensor_telemetry",
  "timestamp_ms": 123456,
  "seq": 42,
  "ultrasonic": {
    "front_mm": 420,
    "front_left_mm": 380,
    "front_right_mm": 450,
    "left_mm": 600,
    "right_mm": 550
  },
  "tof": {
    "angle_deg": 90,
    "distance_mm": 830
  },
  "imu": {
    "yaw_deg": 42.5,
    "gyro_z_rads": 0.12
  }
}
```
*Note: This is an EXAMPLE CONTRACT, not permission to change existing firmware blindly.*

## VisionResult
Owner: Person 2 (Vision / AI)
```json
{
  "station_id": 3,
  "view": "upper",
  "detections": [
    {
      "class": "aphid",
      "category": "pest",
      "confidence": 0.91
    }
  ]
}
```

## EcosystemAssessment
Owner: Person 3 (Ecosystem Intelligence)
```json
{
  "station_id": 3,
  "pdr": 0.42,
  "amri": 0.68,
  "risk": "HIGH",
  "recommendation": "TARGETED_BIOCONTROL"
}
```

## NavigationRequest
Owner: Person 4 (Mission + Dashboard)
```json
{
  "station_id": 4,
  "target": {
    "x": 2.4,
    "y": 1.8
  }
}
```
*NavigationRequest is a HIGH-LEVEL request. It must not be translated directly into raw motor commands by mission code.*

## Station State Lifecycle
Owner: Person 4 (Mission + Dashboard)
- `IDLE`
- `PLAN_MISSION`
- `GO_TO_STATION`
- `ARRIVED`
- `CAPTURE`
- `ANALYZE`
- `FIELD_CARD`
- `NEXT_STATION`
- `COMPLETE`
