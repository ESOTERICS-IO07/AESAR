# FINAL HARDWARE COMMUNICATION AUDIT

## CHECK 1 — BRAIN Wi-Fi SERVER
**Result: PASS**
- **Wi-Fi Network:** `ARACHNID`
- **Password:** `arachnid123`
- **IP Address:** `192.168.4.1`
- **Port:** `80` (TCP via `WiFiServer server(80);`)
- **Incoming Protocol:** Raw TCP socket expecting ASCII strings with newline (`FORWARD\n`, `BACKWARD\n`, etc.)
- **Outgoing Protocol:** Canonical newline-delimited JSON (`sensor_telemetry`)
*Location: `firmware/sensor_esp32/sensor_esp32.ino` (lines 44-49, 169-182)*

## CHECK 2 — SOFTWARE → BRAIN
**Result: PASS**
- `HardwareGateway` correctly connects to `192.168.4.1:80`.
- The gateway sends exactly `FORWARD\n`, `BACKWARD\n`, `LEFT\n`, `RIGHT\n`, and `STOP\n`.
- No JSON is sent to the motor controller.
*Location: `software/backend/hardware/gateway.py` (lines 217-236)*

## CHECK 3 — BRAIN → SOFTWARE
**Result: PASS**
- The Brain sends the unified canonical JSON packet containing all ultrasonic sensors and the ToF scan.
- The `tof_angle_deg` and `tof_distance_mm` are perfectly preserved and dynamically updated every 15ms.
*Location: `firmware/sensor_esp32/sensor_esp32.ino` (lines 170-180)*

## CHECK 4 — BRAIN → ROVER UART
**Result: PASS**
- Brain TX = GPIO 19, Brain RX = GPIO 18
- `sensor_esp32.ino` correctly defines `PIN_UART2_RX = 18` and `PIN_UART2_TX = 19`.
- HardwareSerial is correctly initialized with `Serial2.begin(115200, SERIAL_8N1, PIN_UART2_RX, PIN_UART2_TX);`.
*Location: `firmware/sensor_esp32/sensor_esp32.ino` (lines 36-37, 203)*

## CHECK 5 — ROVER MOTOR CONTROL
**Result: PASS**
- **LEFT:** RPWM 4, LPWM 17, R_EN 23, L_EN 5
- **RIGHT:** RPWM 22, LPWM 21, R_EN 18, L_EN 19
- All pins match exactly.
*Location: `firmware/drive_esp32/drive_esp32.ino` (lines 15-24)*

## CHECK 6 — WATCHDOG
**Result: PASS**
- **Hardware Watchdog:** The `drive_esp32.ino` implements a `1000ms` hardware watchdog (`WATCHDOG_TIMEOUT_MS = 1000`), which reliably protects the rover if no commands arrive.
- **Software Watchdog:** The `HardwareGateway` enforces a secondary `2000ms` software safety timeout. This acts as a stale-state backstop (e.g., if the frontend dies without sending a STOP) but allows normal discrete commands to stay active without continuous resending, avoiding movement stuttering.
*Location: `software/backend/hardware/gateway.py` (lines 287-294) & `firmware/drive_esp32/drive_esp32.ino` (line 32)*

## CHECK 7 — SENSOR PINS
**Result: PASS**
- TRIG: 25
- ECHO FRONT: 32, 45 LEFT: 27, 45 RIGHT: 35, LEFT: 34, RIGHT: 33
- ToF: SDA 21, SCL 22
- Servo: 14
*Location: `firmware/sensor_esp32/sensor_esp32.ino` (lines 20-33)*

## CHECK 8 — SAFETY
**Result: PASS**
- **Path:** E-Stop Triggered -> Backend `RoverStateManager.emergency_stop()` -> `HardwareGateway` executes `await self._write_raw("STOP\n")` -> Brain ESP32 receives `STOP\n` -> Transmits via UART -> Rover ESP32 executes `process_command("STOP")` -> BTS7960 EN pins driven LOW and PWM set to 0.
- Furthermore, if the Wi-Fi disconnects, the Brain ESP32 detects the TCP socket drop and immediately invokes `emergency_stop_motors()`, bypassing the software entirely.
*Location: `software/backend/hardware/gateway.py` (line 251) & `firmware/sensor_esp32/sensor_esp32.ino` (lines 247-251)*

## CHECK 9 — ACTUAL RUN COMMANDS
**Result: PASS**

### Requirements
- **Python Packages:** `fastapi`, `uvicorn`, `websockets`, `pydantic`
- **Environment Variables:** 
  - `ARACHNID_HARDWARE_GATEWAY=real` (Required to use physical hardware rather than the simulator)

### Commands
1. **Start Backend:**
   ```bash
   cd software/backend
   ARACHNID_HARDWARE_GATEWAY=real uvicorn main:app --host 0.0.0.0 --port 8000
   ```
2. **Start Frontend:**
   ```bash
   cd software/frontend
   npm run dev
   ```
3. **Connect to Brain:** Connect the host computer's Wi-Fi network to the SSID `ARACHNID` using password `arachnid123`.
4. **Run Manual Mode:** Open the React UI (e.g. `http://localhost:5173`), ensure the backend is connected to the ESP32 (connection status indicator), and use the on-screen joystick or keyboard controls.
5. **Run Autonomous Mode:** Through the React UI, click the "Autonomous" mode toggle. The backend navigation algorithms will take over command streaming.
