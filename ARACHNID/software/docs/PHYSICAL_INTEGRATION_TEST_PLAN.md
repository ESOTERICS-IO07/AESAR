# ARACHNID — PHYSICAL INTEGRATION TEST PLAN
**Execution Guide for Hardware & ROS2 Bringup**

All tests below are formatted for execution once Person A and the hardware team connect the physical rover.

---

### TEST-001: ESP32 Micro-Controller Connection
- **Purpose**: Verify physical USB/UART connectivity and telemetry stream from the ESP32 board.
- **Preconditions**: ESP32 powered, firmware flashed, connected to compute board.
- **Procedure**: Connect micro-ROS agent or serial bridge on `/dev/ttyUSB0` at 115200 baud.
- **Expected Result**: Ping response received; heartbeat packets published at 10 Hz.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Blocked on Person A / Hardware team firmware flash.

---

### TEST-002: ROS2 Node & DDS Discovery
- **Purpose**: Confirm ROS2 daemon and topics are discoverable by `RealROS2Provider`.
- **Preconditions**: ROS2 Humble/Iron active on compute board.
- **Procedure**: Run `ros2 topic list` and start `RealROS2Provider`.
- **Expected Result**: `GET /api/health` returns `{"status": "ok", "backend": true, "ros2_connected": true}`.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Automated integration test passed against simulated provider.

---

### TEST-003: Front-Left Ultrasonic (`us_fl`) Sensor
- **Purpose**: Verify range acquisition and threshold detection for front-left ultrasonic transceiver.
- **Preconditions**: Rover stationary; target board positioned at 500 mm.
- **Procedure**: Move obstacle between 200 mm and 1500 mm in front-left quadrant.
- **Expected Result**: `us_fl_mm` values match tape measure within ±15 mm; status shows `OK`.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Bounds configured at 20.0 to 4000.0 mm.

---

### TEST-004: Front-Right Ultrasonic (`us_fr`) Sensor
- **Purpose**: Verify range acquisition for front-right ultrasonic transceiver.
- **Preconditions**: Rover stationary; target board positioned at 500 mm.
- **Procedure**: Move obstacle between 200 mm and 1500 mm in front-right quadrant.
- **Expected Result**: `us_fr_mm` values match tape measure within ±15 mm; status shows `OK`.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-005: Left Flank Ultrasonic (`us_l`) Sensor
- **Purpose**: Verify range acquisition for left flank ultrasonic transceiver.
- **Preconditions**: Rover stationary; obstacle placed on left side.
- **Procedure**: Move obstacle between 100 mm and 2000 mm on left side.
- **Expected Result**: `us_l_mm` values match physical distance; UI updates in real-time.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-006: Right Flank Ultrasonic (`us_r`) Sensor
- **Purpose**: Verify range acquisition for right flank ultrasonic transceiver.
- **Preconditions**: Rover stationary; obstacle placed on right side.
- **Procedure**: Move obstacle between 100 mm and 2000 mm on right side.
- **Expected Result**: `us_r_mm` values match physical distance; UI updates in real-time.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-007: Front Time-of-Flight (`tof_front`) Sensor
- **Purpose**: Verify high-speed optical distance sensing on front bumper.
- **Preconditions**: ToF sensor lens clear; target positioned at 300 mm.
- **Procedure**: Move target closer to 50 mm, then pull away to 1500 mm.
- **Expected Result**: `tof_front_mm` updates at 20 Hz with sub-centimeter accuracy.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Maximum optical range: 2000.0 mm.

---

### TEST-008: Real-Time Telemetry Streaming & Freshness
- **Purpose**: Verify end-to-end telemetry packet sequence over WebSocket to Frontend.
- **Preconditions**: Backend and UI connected on `/ws`.
- **Procedure**: Observe sequence number increment and packet latency in UI header.
- **Expected Result**: Packet latency < 100 ms; sequence increments monotonically without drops.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Verified in simulated provider.

---

### TEST-009: Forward Motion Command
- **Purpose**: Verify safe forward driving command execution on motors.
- **Preconditions**: Wheels elevated / unobstructed open floor; low speed set to 0.15 m/s.
- **Procedure**: Press `FORWARD` button or `W` key in UI.
- **Expected Result**: Motor driver drives all wheels forward; command ACK returned.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Safety limit capped at 1.0 m/s.

---

### TEST-010: Backward Motion Command
- **Purpose**: Verify safe reverse driving command execution on motors.
- **Preconditions**: Low speed set to 0.15 m/s.
- **Procedure**: Press `BACKWARD` button or `S` key in UI.
- **Expected Result**: Motor driver drives all wheels in reverse; command ACK returned.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-011: Turn Left Command
- **Purpose**: Verify differential drive left turn execution.
- **Preconditions**: Low angular speed set to 0.3 rad/s.
- **Procedure**: Press `LEFT` button or `A` key in UI.
- **Expected Result**: Left wheels reverse/slow down, right wheels forward; rover pivots counter-clockwise.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-012: Turn Right Command
- **Purpose**: Verify differential drive right turn execution.
- **Preconditions**: Low angular speed set to 0.3 rad/s.
- **Procedure**: Press `RIGHT` button or `D` key in UI.
- **Expected Result**: Right wheels reverse/slow down, left wheels forward; rover pivots clockwise.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-013: Normal Motion Stop
- **Purpose**: Verify standard motor deceleration to zero velocity.
- **Preconditions**: Rover moving slowly.
- **Procedure**: Press `STOP` button or `Spacebar` in UI.
- **Expected Result**: Motors decelerate smoothly to zero velocity; state returns to `IDLE`.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-014: Hardware & Web Emergency Stop (E-Stop)
- **Purpose**: Verify instantaneous motor shutdown and safety latching.
- **Preconditions**: Rover driving.
- **Procedure**: Press the global red `EMERGENCY STOP` button in the UI.
- **Expected Result**: Immediate motor cutoff; state latches to `EMERGENCY_STOP`; all motion commands rejected.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Physical kill switch on rover battery rail must also be independently tested.

---

### TEST-015: Real-Time SLAM / Occupancy Grid Map
- **Purpose**: Verify map updates rendered on Frontend Canvas as rover moves.
- **Preconditions**: Cartographer / SLAM node publishing `/map`.
- **Procedure**: Drive rover through 3m x 3m test arena.
- **Expected Result**: Free space (dark blue) and obstacle walls (red) appear on Canvas map in real-time.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-016: Rover Localization & Heading Marker
- **Purpose**: Verify rover position marker on map matches real physical location.
- **Preconditions**: Odometry `/odom` active.
- **Procedure**: Drive rover in 1-meter square path.
- **Expected Result**: Heading arrow and position dot track rover trajectory accurately.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-017: Waypoint Path Navigation
- **Purpose**: Verify Nav2 path planning trajectory rendering.
- **Preconditions**: Nav2 stack running.
- **Procedure**: Send navigation goal to `[x: 2.0, y: 1.0]`.
- **Expected Result**: Cyan dashed waypoint trajectory line renders from rover to target goal.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-018: Obstacle Avoidance Interlock
- **Purpose**: Verify rover safety stop when distance sensor drops below minimum distance.
- **Preconditions**: Rover moving forward towards solid wall.
- **Procedure**: Allow rover to approach within 300 mm of obstacle.
- **Expected Result**: Proximity warning fires in UI; obstacle avoidance node stops forward drive.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Proximity alert threshold: <400 mm.

---

### TEST-019: Autonomous Frontier Exploration
- **Purpose**: Verify autonomous exploration loop and coverage metrics.
- **Preconditions**: Unexplored arena.
- **Procedure**: Click `START AUTONOMOUS EXPLORATION` in UI.
- **Expected Result**: Frontier count updates; coverage percent increases; rover navigates autonomously.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-020: Hardware Connection Loss
- **Purpose**: Verify safe failure handling when communication cable or WiFi drops.
- **Preconditions**: Rover driving.
- **Procedure**: Disconnect USB/WiFi communication link.
- **Expected Result**: Watchdog triggers safe stop on motors; UI shows `DISCONNECTED` with stale alert.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.

---

### TEST-021: Automatic Reconnection
- **Purpose**: Verify backend and frontend reconnect automatically when hardware link restores.
- **Preconditions**: Disconnected state.
- **Procedure**: Reconnect USB / network link.
- **Expected Result**: `RealROS2Provider` resumes telemetry stream; UI transitions back to `connected`.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: Exponential backoff reconnection loop verified in unit tests.

---

### TEST-022: Battery State of Charge & Power Telemetry
- **Purpose**: Verify battery percentage gauge in UI reflects physical pack voltage.
- **Preconditions**: Battery monitor circuit wired to ESP32 ADC.
- **Procedure**: Verify battery percentage reading on UI header.
- **Expected Result**: Correct percentage displayed (0–100%) with appropriate green/amber/red color badge.
- **Actual Result**: `PENDING PHYSICAL TEST`
- **Status**: `PENDING`
- **Notes**: None.
