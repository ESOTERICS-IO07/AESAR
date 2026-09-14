# ARACHNID Software Integration Contract v1.0.0

## 1. Overview & Architecture Boundaries
The ARACHNID autonomous rover architecture is strictly partitioned into two independent subsystems:
* **Person A (Robotics & Autonomy)**: Firmware, Sensor Acquisition, Filtering, Kinematic Odometry, Complementary Localization, Occupancy Grid Mapping, Frontier Exploration, A* Path Planning, Obstacle Avoidance, Pure Pursuit Velocity Generation, and Motor Serial Bridge.
* **Person B (Backend, Telemetry & UI)**: ROS2-to-Web Bridge, REST API, WebSockets, State DB, Web Dashboard, and User Control Interface.

---

## 2. Coordinate System & Units Standard

* **World Coordinate Frame**: `map`
* **Axes**:
  * $+X$: Forward
  * $+Y$: Left
  * $+Z$: Up
* **Orientation / Yaw**:
  * Radians counter-clockwise from $+X$ axis.
  * Range: $[-\pi, \pi]$
  * No degrees allowed in ROS2 topics.
* **Navigation Units**:
  * Distance / Position: Metres ($m$)
  * Velocities: Metres per second ($m/s$), Radians per second ($rad/s$)
  * Time: Milliseconds ($ms$) since epoch / startup
* **Hardware Boundary Units**:
  * Distance: Millimetres ($mm$) for ultrasonic and Time-of-Flight sensors.
  * Acceleration: $m/s^2$
  * Angular Velocity: $rad/s$

---

## 3. ROS2 Topics & Schemas (Single Source of Truth)

### 3.1 `/sensors/range` (`RangePacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "seq": 1042,
  "us_fc_mm": 450.0,
  "us_fl_mm": 450.0,
  "us_fr_mm": 462.0,
  "us_l_mm": 1200.0,
  "us_r_mm": 1180.0,
  "tof_front_mm": 445.0,
  "sensor_status": {
    "us_fc": "OK",
    "us_fl": "OK",
    "us_fr": "OK",
    "us_l": "OK",
    "us_r": "OK",
    "tof_front": "OK"
  }
}
```

### 3.2 `/imu/data` (`ImuPacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "seq": 1042,
  "accel_x_mps2": 0.02,
  "accel_y_mps2": -0.01,
  "accel_z_mps2": 9.81,
  "gyro_x_rads": 0.001,
  "gyro_y_rads": -0.002,
  "gyro_z_rads": 0.000
}
```

### 3.3 `/odom` (`OdometryPacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "x_m": 0.352,
  "y_m": 0.114,
  "yaw_rad": 0.185,
  "linear_velocity_mps": 0.200,
  "angular_velocity_rads": 0.050,
  "left_ticks": 1420,
  "right_ticks": 1465
}
```

### 3.4 `/robot_pose` (`PosePacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "frame": "map",
  "x_m": 0.352,
  "y_m": 0.114,
  "yaw_rad": 0.185,
  "confidence": 0.98
}
```

### 3.5 `/map` (`OccupancyGridPacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "frame": "map",
  "resolution_m_per_cell": 0.05,
  "width": 200,
  "height": 200,
  "origin_x_m": -5.0,
  "origin_y_m": -5.0,
  "data": [-1, 0, 100, ...]
}
```
*Cell values*: `-1` = Unknown, `0` = Free, `100` = Occupied. Total cells = $200 \times 200 = 40000$.

### 3.6 `/frontiers` (`FrontierPacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "frontiers": [
    {
      "id": "F-001",
      "x_m": 1.25,
      "y_m": 0.85,
      "distance_m": 1.51,
      "score": 1.85,
      "status": "SELECTED"
    },
    {
      "id": "F-002",
      "x_m": -0.80,
      "y_m": 2.10,
      "distance_m": 2.25,
      "score": 0.92,
      "status": "CANDIDATE"
    }
  ]
}
```

### 3.7 `/planned_path` (`PathPacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "status": "NAVIGATING",
  "target_id": "F-001",
  "points": [
    {"x_m": 0.35, "y_m": 0.11, "yaw_rad": 0.18},
    {"x_m": 0.50, "y_m": 0.25, "yaw_rad": 0.35},
    {"x_m": 1.25, "y_m": 0.85, "yaw_rad": 0.65}
  ]
}
```

### 3.8 `/cmd_vel` (`VelocityCommand`)
```json
{
  "command_id": "CMD-1042",
  "timestamp_ms": 1725200000123,
  "linear_mps": 0.250,
  "angular_rads": 0.150,
  "source": "AUTONOMY"
}
```

### 3.9 `/robot_state` (`RobotStatePacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "robot_mode": "AUTONOMOUS",
  "nav_status": "NAVIGATING",
  "safety_status": "NORMAL",
  "battery_percent": 95.0
}
```

### 3.10 `/robot_errors` (`RobotError`)
```json
{
  "timestamp_ms": 1725200000123,
  "component": "sensor_interface",
  "code": "SENSOR_TIMEOUT",
  "severity": "WARNING",
  "message": "Sensor serial port communication timed out",
  "latched": false
}
```

### 3.11 `/emergency_stop` (`EmergencyStopPacket`)
```json
{
  "timestamp_ms": 1725200000123,
  "stop": true,
  "source": "OPERATOR"
}
```

---

## 4. Contract Enums

### Robot Mode
* `DISCONNECTED`
* `IDLE`
* `MANUAL`
* `AUTONOMOUS`
* `PAUSED`
* `EMERGENCY_STOP`
* `ERROR`

### Navigation Status
* `IDLE`
* `SELECTING_FRONTIER`
* `PLANNING`
* `NAVIGATING`
* `OBSTACLE_BLOCKED`
* `TARGET_REACHED`
* `NO_PATH`
* `COMPLETE`
* `ERROR`

### Safety Status
* `NORMAL`
* `WARNING`
* `STOP_REQUESTED`
* `EMERGENCY_STOP`
* `HARDWARE_FAULT`

### Frontier Status
* `CANDIDATE`
* `SELECTED`
* `REACHED`
* `REJECTED`
* `STALE`
