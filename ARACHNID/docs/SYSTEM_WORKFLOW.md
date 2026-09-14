# ARACHNID System Workflow & Node Architecture

## 1. System Overview
The ARACHNID autonomous rover executes fully autonomous exploration, mapping, and navigation through an interconnected pipeline of ROS2 nodes and dual ESP32 microcontrollers.

```
                           [ Physical Environment ]
                                │            │
                      ┌─────────┴──┐      ┌──┴─────────┐
                      │Sensor ESP32│      │ Drive ESP32│
                      └─────┬──────┘      └───▲────────┘
                     UART   │ (Range/IMU) UART│ (Drive Cmds)
                            ▼                 │
                  ┌──────────────────┐  ┌─────┴────────┐
                  │ sensor_interface │  │ motor_bridge │
                  └────────┬─────────┘  └─────▲────────┘
                           │                  │
         ┌─────────────────┼────────────┐     │ /cmd_vel
         │ /sensors/range  │ /imu/data  │     │
         ▼                 ▼            │     │
   ┌──────────┐     ┌──────────────┐    │     │
   │ odometry │────►│ localization │    │     │
   └────┬─────┘     └──────┬───────┘    │     │
        │ /odom            │ /robot_pose│     │
        └─────────┬────────┴────────────┘     │
                  │                           │
            ┌─────┴──────┐                    │
            │  mapping   │                    │
            └─────┬──────┘                    │
                  │ /map                      │
            ┌─────┴──────┐                    │
            │exploration │                    │
            └─────┬──────┘                    │
                  │ /frontiers                │
            ┌─────┴──────┐                    │
            │ navigation │────────────────────┘
            └────────────┘
        /planned_path, /cmd_vel
```

---

## 2. Autonomy Lifecycle States

### Robot Modes
1. **`DISCONNECTED`**: Hardware UART links uninitialized.
2. **`IDLE`**: Ready and listening for autonomy or manual commands.
3. **`MANUAL`**: Manual teleoperation mode (overriding autonomy).
4. **`AUTONOMOUS`**: Active frontier exploration and path following.
5. **`PAUSED`**: Rover temporarily halted, maintaining map state.
6. **`EMERGENCY_STOP`**: Immediate zero-velocity safety shutdown latched.
7. **`ERROR`**: Hardware fault or sensor failure condition.

### Navigation State Machine
```
   [ IDLE ] ──► [ SELECTING_FRONTIER ] ──► [ PLANNING (A*) ]
                        ▲                         │
                        │ Path Complete / Reached │ Path Found
                        │                         ▼
               [ TARGET_REACHED ] ◄─────── [ NAVIGATING ]
                                                  │
                                                  │ Obstacle < 0.18m
                                                  ▼
                                         [ OBSTACLE_BLOCKED ]
                                                  │
                                                  ▼ Replan
                                         [ SELECTING_FRONTIER ]
```
