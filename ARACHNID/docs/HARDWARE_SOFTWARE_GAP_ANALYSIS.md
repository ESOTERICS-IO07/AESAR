# ARACHNID Rover: Hardware vs Software Gap Analysis

This document identifies critical gaps and inconsistencies between the physically assembled ARACHNID hardware and the current state of the software/firmware repository.

## 1. Current Firmware Architecture
- **Two-ESP32 System**:
  - **ESP32 #1 (Drive)**: Controls two BTS7960 motor drivers for 4 motors. Implements a 500ms safety watchdog and expects wheel encoder inputs.
  - **ESP32 #2 (Sensor/Brain)**: Handles 5 ultrasonic sensors and 1 I2C ToF sensor. Hosts a Wi-Fi SoftAP (192.168.4.1) and acts as a transparent TCP-to-UART bridge to the Drive ESP32. It also includes code for an MPU6050 IMU.

## 2. Current ESP32 Pin Definitions
**Drive ESP32 (Firmware vs Hardware)**:
- **Left BTS7960**:
  - *Firmware*: RPWM=12, LPWM=13, EN=14 (single enable).
  - *Hardware*: RPWM=4, LPWM=17, R_EN=23, L_EN=5.
- **Right BTS7960**:
  - *Firmware*: RPWM=27, LPWM=32, EN=33 (single enable).
  - *Hardware*: RPWM=22, LPWM=21, R_EN=18, L_EN=19.

**Sensor ESP32 (Firmware vs Hardware)**:
- **Ultrasonics**:
  - *Firmware*: TRIG=25. Echoes: 32(Front), 27(45L), 35(45R), 34(Left), 33(Right).
  - *Hardware*: TRIG=25. Echoes: 32(Front), 27(45L), 35(45R), 34(Left), 33(Right). (Pins match, but field names vary).
- **ToF & Servo**:
  - *Firmware*: SDA=21, SCL=22. NO servo configured.
  - *Hardware*: SDA=21, SCL=22. Servo on GPIO 14.

## 3. Current Serial Protocol
- **Baud Rate**: 115200 for both.
- **Hardware Expectation**: The physical drive unit currently expects ASCII commands (`FORWARD`, `BACKWARD`, `LEFT`, `RIGHT`, `STOP`).
- **Firmware Expectation**: `drive_esp32.ino` expects JSON packets (e.g., `{"left_mps": 0.2, "right_mps": 0.2, "e_stop": false}`).
- **Backend Transmission**: `esp32_provider.py` sends BOTH JSON velocity strings and ASCII strings back-to-back, creating parsing risks.

## 4. Current Backend Architecture
- **FastAPI / ROS 2 Hybrid**: Exposes WebSocket endpoints for the frontend and maintains ROS 2 adapters.
- **ESP32 Provider**: A TCP client (`esp32_provider.py`) connects to the Sensor ESP32's SoftAP (192.168.4.1:80), parses telemetry JSON, updates rover state, and sends down control commands.
- **Simulator**: `engine.py` provides a kinematic and environmental simulator for offline testing.

## 5. Current Frontend Architecture
- **React + TypeScript**: Connects to the backend via WebSockets (`useRover.tsx`).
- **Dashboards**: Displays telemetry, maps, and allows sending navigation/manual commands.

## 6. Current Mapping Architecture
- **Real-time Occupancy Grid**: Managed in `esp32_provider.py`. It uses Bresenham's line algorithm to raycast from the robot's origin to the ToF sensor hit point.
- **Grid Specs**: 200x200 grid at 0.05m resolution.

## 7. Current Navigation Architecture
- **Path Planning**: The backend defines a `NavigationAdapter` and paths are represented as a list of 2D points. Currently heavily simulated in `engine.py`.

## 8. Current Localization / Odometry Assumptions
- The software assumes a differential drive model with wheel encoders providing left and right tick counts. This is expected to compute position (`x`, `y`) and heading (`theta`). Since no encoders exist in hardware, localization relies entirely on dead-reckoning or is effectively non-functional.

## 9. Assumptions of Wheel Encoders
- `firmware/drive_esp32/drive_esp32.ino`: Defines interrupt pins (34, 35, 36, 39) for quadrature encoders and publishes `left_ticks` / `right_ticks` in telemetry JSON.
- `software/config/hardware.yaml` & `interfaces.yaml`: Configures encoders as enabled.
- **Hardware Reality**: NO wheel encoders exist.

## 10. Assumptions of IMU
- `firmware/sensor_esp32/sensor_esp32.ino`: Initializes an Adafruit MPU6050 and publishes `accel` and `gyro` data at 20Hz.
- `software/config/hardware.yaml` & `interfaces.yaml`: Explicitly marks IMU as enabled.
- `software/frontend/src/App.tsx`: Attempts to parse and display IMU data.
- **Hardware Reality**: NO IMU exists.

## 11. Motor Pinout Gaps
- `firmware/drive_esp32/drive_esp32.ino`: Assumes only one `EN` pin per BTS7960 driver (Pins 14 and 33).
- **Hardware Reality**: The physical assembly utilizes *both* `L_EN` and `R_EN` for each BTS7960 (Left: 23, 5 | Right: 18, 19) and different PWM pins (Left: 4, 17 | Right: 22, 21).

## 12. Command Format Gaps (JSON vs ASCII)
- `firmware/drive_esp32/drive_esp32.ino`: Requires `{"left_mps": X, "right_mps": Y}` via `deserializeJson()`.
- `software/backend/ros2/esp32_provider.py`: Sends JSON strings followed immediately by ASCII commands (`FORWARD\n`).
- **Hardware Reality**: Physical tests were performed successfully with ASCII string commands, meaning the `drive_esp32.ino` currently in the repo does not match the compiled binary on the actual drive board.

## 13. ToF Sensor: Fixed vs Servo-Scanned
- `firmware/sensor_esp32/sensor_esp32.ino`: Interrogates a fixed ToF sensor (`lox.rangingTest()`) and outputs a static `tof_front_mm` field. No servo code exists.
- `software/backend/ros2/esp32_provider.py`: Listens for dynamic `MAP,angle,dist` strings or JSON `tof_scan` arrays with `angle_deg` to build the occupancy map.
- **Hardware Reality**: The ToF is physically mounted on a servo (GPIO 14), but firmware completely ignores the servo and acts like the ToF is static.

## 14. Ultrasonic Telemetry Name Discrepancies
- **Firmware Names**: `us_fc_mm` (front), `us_fl_mm` (45L), `us_fr_mm` (45R), `us_l_mm` (left), `us_r_mm` (right).
- **Software Config (`hardware.yaml`)**: Declares only 4 sensors: `us_fl`, `us_fr`, `us_l`, `us_r`.
- **Backend Parsing**: Looks for `us_front_mm`, `us_fc_mm`, `us_fl_mm` but maps them confusingly.

## 15. Dangerous or Contradictory Implementation
1. **Safety Watchdog vs ASCII Commands**: `drive_esp32.ino` implements a 500ms watchdog that stops motors if no JSON is received. If the real hardware is running on ASCII commands, the JSON-based watchdog in the repo code is either not deployed or broken.
2. **Double Command Transmission**: `esp32_provider.py` sends `await self._write_raw(json.dumps(payload) + "\n")` AND `await self._write_raw(cmd_str + "\n")`. Sending non-JSON strings to a JSON parser will cause ArduinoJson to fail and potentially drop packets, making movement unreliable.
3. **Emergency Stop Bypass**: `sensor_esp32.ino` defines `emergency_stop_motors()` that sends `{"e_stop":true}` to the Drive ESP32. If the Drive ESP32 only understands ASCII `STOP`, the emergency stop will fail to trigger.
4. **Enable Pins tied incorrectly**: The repo firmware uses a single enable pin per motor driver. The physical hardware requires both `L_EN` and `R_EN` to be pulled HIGH for the BTS7960 to output voltage. If the repo code is uploaded, the motors will likely not spin.
