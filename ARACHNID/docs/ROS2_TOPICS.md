# ARACHNID ROS2 Topic Directory & Schema Reference

All topics strictly adhere to the **ARACHNID Software Integration Contract v1.0.0**.

| Topic Name | Publisher Node | Subscriber Nodes | Message Type / Schema | Rate |
|---|---|---|---|---|
| `/sensors/range` | `sensor_interface_node` | `odometry_node`, `occupancy_grid_node`, `planner_node` | `std_msgs/String` (`RangePacket`) | 20 Hz |
| `/imu/data` | `sensor_interface_node` | `odometry_node`, `localization_node` | `std_msgs/String` (`ImuPacket`) | 20 Hz |
| `/odom` | `odometry_node` | `localization_node` | `std_msgs/String` (`OdometryPacket`) | 20 Hz |
| `/robot_pose` | `localization_node` | `occupancy_grid_node`, `exploration_manager`, `planner_node` | `std_msgs/String` (`PosePacket`) | 20 Hz |
| `/map` | `occupancy_grid_node` | `exploration_manager`, `planner_node` | `std_msgs/String` (`OccupancyGridPacket`) | 5 Hz |
| `/frontiers` | `exploration_manager` | `planner_node` | `std_msgs/String` (`FrontierPacket`) | 2 Hz |
| `/planned_path` | `planner_node` | External Bridges / RViz | `std_msgs/String` (`PathPacket`) | 20 Hz |
| `/cmd_vel` | `planner_node` | `motor_bridge_node` | `std_msgs/String` (`VelocityCommand`) | 20 Hz |
| `/robot_state` | `planner_node` | External Bridges / UI | `std_msgs/String` (`RobotStatePacket`) | 20 Hz |
| `/robot_errors` | All Nodes | Diagnostics / UI | `std_msgs/String` (`RobotError`) | Event |
| `/emergency_stop` | Safety System / UI | `planner_node`, `motor_bridge_node` | `std_msgs/String` (`EmergencyStopPacket`) | Event |

---

## Complete Packet Schemas

### 1. `RangePacket` (`/sensors/range`)
```json
{
  "timestamp_ms": 1725200000000,
  "seq": 1042,
  "us_fl_mm": 450.0,
  "us_fr_mm": 462.0,
  "us_l_mm": 1200.0,
  "us_r_mm": 1180.0,
  "tof_front_mm": 445.0,
  "sensor_status": {
    "us_fl": "OK",
    "us_fr": "OK",
    "us_l": "OK",
    "us_r": "OK",
    "tof_front": "OK"
  }
}
```

### 2. `ImuPacket` (`/imu/data`)
```json
{
  "timestamp_ms": 1725200000000,
  "seq": 1042,
  "accel_x_mps2": 0.02,
  "accel_y_mps2": -0.01,
  "accel_z_mps2": 9.806,
  "gyro_x_rads": 0.001,
  "gyro_y_rads": -0.002,
  "gyro_z_rads": 0.000
}
```

### 3. `OdometryPacket` (`/odom`)
```json
{
  "timestamp_ms": 1725200000000,
  "x_m": 0.352,
  "y_m": 0.114,
  "yaw_rad": 0.185,
  "linear_velocity_mps": 0.200,
  "angular_velocity_rads": 0.050,
  "left_ticks": 1420,
  "right_ticks": 1465
}
```

### 4. `PosePacket` (`/robot_pose`)
```json
{
  "timestamp_ms": 1725200000000,
  "frame": "map",
  "x_m": 0.352,
  "y_m": 0.114,
  "yaw_rad": 0.185,
  "confidence": 0.98
}
```

### 5. `OccupancyGridPacket` (`/map`)
```json
{
  "timestamp_ms": 1725200000000,
  "frame": "map",
  "resolution_m_per_cell": 0.05,
  "width": 200,
  "height": 200,
  "origin_x_m": -5.0,
  "origin_y_m": -5.0,
  "data": [-1, 0, 100, ...]
}
```

### 6. `FrontierPacket` (`/frontiers`)
```json
{
  "timestamp_ms": 1725200000000,
  "frontiers": [
    {
      "id": "F-001",
      "x_m": 1.25,
      "y_m": 0.85,
      "distance_m": 1.51,
      "score": 1.85,
      "status": "SELECTED"
    }
  ]
}
```

### 7. `PathPacket` (`/planned_path`)
```json
{
  "timestamp_ms": 1725200000000,
  "status": "NAVIGATING",
  "target_id": "F-001",
  "points": [
    {"x_m": 0.35, "y_m": 0.11, "yaw_rad": 0.18},
    {"x_m": 1.25, "y_m": 0.85, "yaw_rad": 0.65}
  ]
}
```

### 8. `VelocityCommand` (`/cmd_vel`)
```json
{
  "command_id": "CMD-000104",
  "timestamp_ms": 1725200000000,
  "linear_mps": 0.250,
  "angular_rads": 0.150,
  "source": "AUTONOMY"
}
```

### 9. `RobotError` (`/robot_errors`)
```json
{
  "timestamp_ms": 1725200000000,
  "component": "sensor_interface",
  "code": "SERIAL_TIMEOUT",
  "severity": "WARNING",
  "message": "Sensor serial timed out",
  "latched": false
}
```
