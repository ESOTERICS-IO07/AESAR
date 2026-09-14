# ARACHNID — ROS2 & HARDWARE INTEGRATION HANDOFF
**Person B &rarr; Person A (Robotics) & Hardware Team**

This document specifies the exact contract interface boundaries between the ARACHNID Backend/Web Command Center (Person B) and the ROS2 Navigation/Hardware Firmware Stack (Person A & Hardware Team).

---

## 1. Interface Specification Table

| Logical Interface | ROS2 Topic | ROS2 Message Type | Direction | Fields | Units | Expected Rate | Frame | Valid Range | Owner | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Front-Left Ultrasonic** | `TBD — PERSON A` | `sensor_msgs/Range` | Robot &rarr; Backend | `range`, `min_range`, `max_range` | mm (or m adapted by backend) | 10 Hz | `us_fl_link` | 20.0 to 4000.0 mm | Person A / Hardware | CONTRACT LOCKED |
| **Front-Right Ultrasonic** | `TBD — PERSON A` | `sensor_msgs/Range` | Robot &rarr; Backend | `range`, `min_range`, `max_range` | mm (or m adapted by backend) | 10 Hz | `us_fr_link` | 20.0 to 4000.0 mm | Person A / Hardware | CONTRACT LOCKED |
| **Left Flank Ultrasonic** | `TBD — PERSON A` | `sensor_msgs/Range` | Robot &rarr; Backend | `range`, `min_range`, `max_range` | mm (or m adapted by backend) | 10 Hz | `us_l_link` | 20.0 to 4000.0 mm | Person A / Hardware | CONTRACT LOCKED |
| **Right Flank Ultrasonic** | `TBD — PERSON A` | `sensor_msgs/Range` | Robot &rarr; Backend | `range`, `min_range`, `max_range` | mm (or m adapted by backend) | 10 Hz | `us_r_link` | 20.0 to 4000.0 mm | Person A / Hardware | CONTRACT LOCKED |
| **Front Time-of-Flight** | `TBD — PERSON A` | `sensor_msgs/Range` | Robot &rarr; Backend | `range`, `min_range`, `max_range` | mm (or m adapted by backend) | 20 Hz | `tof_front_link` | 10.0 to 2000.0 mm | Person A / Hardware | CONTRACT LOCKED |
| **Combined Telemetry** | `/arachnid/sensors/telemetry` | `arachnid_msgs/Telemetry` or JSON | Robot &rarr; Backend | `us_fl_mm`, `us_fr_mm`, `us_l_mm`, `us_r_mm`, `tof_front_mm` | mm | 10 Hz | `base_link` | Configured sensor bounds | Person A / Person B | READY |
| **Robot Pose / Odometry** | `/odom` | `nav_msgs/Odometry` | Robot &rarr; Backend | `pose.pose.position.x/y`, `pose.pose.orientation` | meters, radians | 20 Hz | `odom` &rarr; `base_link` | Unbounded | Person A | CONTRACT LOCKED |
| **Occupancy Grid Map** | `/map` | `nav_msgs/OccupancyGrid` | ROS2 &rarr; Backend | `info.resolution`, `info.width`, `info.height`, `info.origin`, `data` (int8[]) | m/cell, cells | 1–2 Hz | `map` | 0 (free), 100 (obstacle), -1 (unknown) | Person A | CONTRACT LOCKED |
| **Navigation Path** | `/plan` | `nav_msgs/Path` | ROS2 &rarr; Backend | `poses[]` (geometry_msgs/PoseStamped) | meters | On change | `map` | Waypoint array | Person A | CONTRACT LOCKED |
| **Navigation Goal** | `TBD — PERSON A` | `geometry_msgs/PoseStamped` | Backend &rarr; ROS2 | `pose.position.x/y` | meters | On operator goal | `map` | In map bounds | Person B &rarr; Person A | CONTRACT LOCKED |
| **Frontier Exploration** | `TBD — PERSON A` | `arachnid_msgs/Exploration` | ROS2 &rarr; Backend | `status`, `explored_percent`, `frontier_count`, `current_goal` | percent, count, [x,y] | 2 Hz | `map` | 0.0–100.0% | Person A | CONTRACT LOCKED |
| **Battery Status** | `TBD — PERSON A` | `sensor_msgs/BatteryState` | Robot &rarr; Backend | `percentage` (0.0 to 1.0) | percent | 1 Hz | `base_link` | 0.0–100.0% | Hardware / Person A | CONTRACT LOCKED |
| **Rover System State** | `/rover/status` | `arachnid_msgs/RoverStatus` | Backend &harr; ROS2 | `connected`, `state`, `mode`, `battery_percent` | enums | 2 Hz | `base_link` | Contract Enums | Person B &rarr; Person A | CONTRACT LOCKED |
| **Velocity Commands** | `/cmd_vel` | `geometry_msgs/Twist` | Backend &rarr; ROS2 | `linear.x` (m/s), `angular.z` (rad/s) | m/s, rad/s | 10–20 Hz | `base_link` | Linear: 0.05–1.0 m/s, Angular: 0.1–1.5 rad/s | Person B &rarr; Person A | CONTRACT LOCKED |
| **Emergency Stop** | `/emergency_stop` | `std_msgs/Bool` or Hardware Pin | Backend &rarr; Hardware | `data: true` | Boolean | Immediate | Global | Latching STOP | Hardware / Person A | CONTRACT LOCKED |

---

## 2. Sensor Orientation & Frame Offsets

```
                 ▲ Forward (Heading / +X in robot frame)
                 │
              [ToF Front] (0°)
                 │
   [us_fl] (45°) │ [us_fr] (-45°)
          \      │      /
           ┌─────┴─────┐
           │  ARACHNID │
[us_l] ────┤   ROVER   ├──── [us_r]
 (90°)     │   CHASSIS │     (-90°)
           └───────────┘
                 │
                 ▼ Backward (-X)
```

---

## 3. Communication Bridge Execution Sequence

1. **Micro-ROS / Serial Bringup**:
   - ESP32 connects to computing unit via USB UART / SPI / micro-ROS agent.
2. **ROS2 Node Launch**:
   - `ros2 launch arachnid_bringup rover_full.launch.py`
3. **Backend Launch**:
   - Set `ARACHNID_ROS2_PROVIDER=real`
   - Start backend: `python -m uvicorn backend.main:app --host 0.0.0.0 --port 8100`
4. **WebSocket Command Center**:
   - Start UI: `npm run dev` / `npm run preview` on `http://127.0.0.1:5173`
