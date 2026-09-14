# Person A (Robotics & Autonomy) Architecture Document

## 1. System Architecture Overview

```
                          [ Physical Hardware ]
                     Ultrasonics, ToF, IMU, Encoders, Motors
                                  │           │
                    ┌─────────────┴─┐       ┌─┴─────────────┐
                    │ Sensor ESP32  │       │  Drive ESP32  │
                    └───────┬───────┘       └───────▲───────┘
                     Serial │ (Range/IMU)    Serial │ (Motor Cmds)
                            ▼                       │
                  ┌──────────────────┐    ┌─────────────────┐
                  │ sensor_interface │    │  motor_bridge   │
                  └────────┬─────────┘    └────────▲────────┘
                           │                       │
          ┌────────────────┼──────────────┐        │ /cmd_vel
          │ /sensors/range │ /imu/data    │        │
          ▼                ▼              │        │
    ┌──────────┐     ┌──────────────┐     │        │
    │ odometry │────►│ localization │     │        │
    └────┬─────┘     └──────┬───────┘     │        │
         │ /odom            │ /robot_pose │        │
         └─────────┬────────┴─────────────┘        │
                   │                               │
             ┌─────┴──────┐                        │
             │  mapping   │                        │
             └─────┬──────┘                        │
                   │ /map                          │
             ┌─────┴──────┐                        │
             │exploration │                        │
             └─────┬──────┘                        │
                   │ /frontiers                    │
             ┌─────┴──────┐                        │
             │ navigation │────────────────────────┘
             └────────────┘
         /planned_path, /cmd_vel
```

## 2. Package Descriptions & Lifecycles

### 2.1 `sensor_interface`
* **Node**: `sensor_node`
* **Inputs**: Serial data stream from Sensor ESP32 (`COM6` / `/dev/ttyUSB0`)
* **Filtering**:
  * Median Filter (window=5) for 4 Ultrasonic sensors (`us_fl`, `us_fr`, `us_l`, `us_r`)
  * Moving Average Filter (window=5) for ToF sensor (`tof_front`)
  * Low-Pass Filter ($\alpha=0.25$) for IMU 3-axis Accelerometer & Gyroscope
* **Outputs**: `/sensors/range`, `/imu/data`, `/robot_errors`

### 2.2 `odometry`
* **Node**: `odometry_node`
* **Inputs**: `/sensors/range` (or encoder telemetry), `/imu/data`
* **Kinematics**: Differential drive wheel odometry with delta tick processing, linear and angular velocity calculations, and IMU gyro rate integration.
* **Outputs**: `/odom`

### 2.3 `localization`
* **Node**: `localization_node`
* **Inputs**: `/odom`, `/imu/data`
* **Fusion**: Complementary filter blending integrated high-rate gyro heading with wheel odometry heading, bounding confidence metric based on slip and sensor health.
* **Outputs**: `/robot_pose` (`frame: "map"`)

### 2.4 `mapping`
* **Node**: `occupancy_grid_node`
* **Inputs**: `/robot_pose`, `/sensors/range`
* **Grid Space**: $200 \times 200$ cells, $0.05\text{ m/cell}$ resolution, origin $[-5.0\text{ m}, -5.0\text{ m}]$.
* **Ray Casting**: Bresenham line algorithm with exact sensor mounting translations and angular offsets.
* **Outputs**: `/map`

### 2.5 `exploration`
* **Node**: `exploration_manager`
* **Inputs**: `/map`, `/robot_pose`
* **Frontier Detection**: 8-neighbor scan identifying free cells ($0$) adjacent to unknown cells ($-1$), clustered into candidate frontiers.
* **Selection**: Deterministic metric weighting distance in world coordinates against cluster information value, selecting optimal target.
* **Outputs**: `/frontiers`

### 2.6 `navigation`
* **Node**: `planner_node`
* **Inputs**: `/frontiers`, `/robot_pose`, `/map`, `/sensors/range`, `/emergency_stop`
* **Path Planning**: 8-connected grid A* path search with obstacle inflation safety barrier.
* **Controller**: Proportional pure pursuit velocity generator outputting velocity commands bounded by configured kinematics.
* **Safety**: Active obstacle avoidance slowdown and immediate zero-velocity lock on `/emergency_stop`.
* **Outputs**: `/planned_path`, `/cmd_vel` (`source: "AUTONOMY"`), `/robot_state`, `/robot_errors`

### 2.7 `motor_bridge`
* **Node**: `motor_bridge_node`
* **Inputs**: `/cmd_vel`, `/emergency_stop`
* **Hardware Output**: Serial commands to Drive ESP32 (`COM5` / `/dev/ttyUSB1`)
* **Watchdog**: 500ms timeout triggering zero-velocity stop if commands cease.
* **Emergency Stop**: Immediate hardware kill command.
* **Outputs**: `/robot_errors`
