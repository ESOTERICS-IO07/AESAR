# ARACHNID: Autonomous Reconnaissance, Adaptive Computation, Hazard Navigation & Intelligent Discovery

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python)](https://www.python.org/)
[![Hardware](https://img.shields.io/badge/Hardware-Dual%20ESP32%20%2B%20BTS7960-e67e22)](#hardware-architecture--limitations)
[![ROS 2](https://img.shields.io/badge/ROS%202-Legacy%20%2F%20Reference-lightgrey)](#legacy--reference-architecture-ros2_ws)

ARACHNID is a four-wheel differential-drive autonomous exploration and teleoperation rover platform engineered for obstacle avoidance, 2D occupancy grid mapping, real-time telemetry streaming, and remote mission control.

The current working production software stack uses a **FastAPI backend + React frontend communicating directly over Wi-Fi** with a dual-ESP32 embedded hardware architecture.

> [!IMPORTANT]
> **ROS 2 (`ros2_ws/`) is a Legacy / Reference Architecture — not required for the current ARACHNID runtime.**
> The current working system does not use ROS 2, `rclpy`, or `rosbridge`. The rover is fully operated via the Python FastAPI backend and React frontend over a direct TCP Wi-Fi connection.

---

## Production Runtime Architecture (Primary)

The primary, working runtime architecture operates directly between the host machine (laptop/PC) and the rover's on-board microcontrollers without any middleware or Single Board Computer (SBC) dependencies:

```
React Frontend (Vite + TypeScript)
    ↕ HTTP / WebSocket
FastAPI Backend (Python 3.10+)
    ↕ Wi-Fi TCP (192.168.4.1:80)
Brain ESP32 #2 (SoftAP + 5x Ultrasonics + Servo-swept ToF)
    ↕ UART (115200 baud: Brain TX 19 → Rover RX 26 | Brain RX 18 ← Rover TX 25)
Rover ESP32 #1 (Drive Controller + 1000ms Watchdog)
    ↓
BTS7960 H-Bridges → 4x DC Motors
```

### Data & Command Flow:
1. **Sensor Telemetry**: Brain ESP32 #2 reads 5 ultrasonic distance sensors and sweeps a VL53L0X Time-of-Flight (ToF) rangefinder dynamically across approximately **30°–150°**, transmitting unified JSON telemetry lines over Wi-Fi TCP to the FastAPI backend.
2. **Backend Processing**: The Python FastAPI backend (`HardwareGateway`) receives telemetry, updates internal 2D occupancy grid mapping via raycasting, performs safety proximity monitoring (180mm safety stop), and tracks rover telemetry.
3. **Frontend Visualization**: Live state, sensor distances, safety alerts, and map grids stream to the React mission control dashboard over WebSockets.
4. **Motion Control**: User manual teleoperation or autonomous navigation commands pass through the backend's `SafetyManager`, are translated into discrete ASCII commands (`FORWARD\n`, `BACKWARD\n`, `LEFT\n`, `RIGHT\n`, `STOP\n`), transmitted via Wi-Fi TCP to Brain ESP32 #2, and relayed over UART to Rover ESP32 #1.
5. **Hardware Safety**: Rover ESP32 #1 drives dual BTS7960 motor controllers with a strict **1000ms command timeout watchdog** and immediate hardware E-stop latching.

---

## Hardware Architecture & Limitations

The physical rover operates using **two ESP32 microcontroller boards**:

| Controller | Physical Role | Primary Interfaces | Safety Features |
| :--- | :--- | :--- | :--- |
| **Brain ESP32 #2** | Sensor acquisition, Wi-Fi SoftAP host (`192.168.4.1:80`), UART bridge | 5x Ultrasonic sensors, VL53L0X ToF on Servo (GPIO 14), UART (TX: 19, RX: 18) | Automated proximity halt (<180mm), connection monitoring |
| **Rover ESP32 #1** | Motor speed & directional control, BTS7960 PWM | Dual BTS7960 43A H-Bridges (4 DC motors), UART (RX: 26, TX: 25) | 1000ms communication timeout watchdog, hard E-stop latch |

### Communication Protocols
- **Wi-Fi SoftAP (Brain ESP32 #2)**:
  - **SSID**: `ARACHNID`
  - **Password**: `arachnid123`
  - **IP**: `192.168.4.1`
  - **TCP Port**: `80`
- **UART Link (Brain ESP32 #2 ↔ Rover ESP32 #1)**:
  - **Baud Rate**: `115200` baud (8N1)
  - **Wiring**: Brain TX (GPIO 19) $\rightarrow$ Rover RX (GPIO 26) ; Brain RX (GPIO 18) $\leftarrow$ Rover TX (GPIO 25)
  - **Commands**: `FORWARD\n`, `BACKWARD\n`, `LEFT\n`, `RIGHT\n`, `STOP\n`

### Sensors & Actuators
- **5x Ultrasonic Sensors (HC-SR04 / JSN-SR04T)**: Directional range detection around the chassis:
  - `us_fc`: Front Center ($0^\circ$)
  - `us_fl`: Front Left ($+45^\circ$)
  - `us_fr`: Front Right ($-45^\circ$)
  - `us_l`: Side Left ($+90^\circ$)
  - `us_r`: Side Right ($-90^\circ$)
- **1x VL53L0X Time-of-Flight (ToF) Sensor**: Mounted on a front micro-servo scanning dynamically across approximately **30° to 150°**, providing forward distance-angle profiling for real-time 2D occupancy mapping.
- **Dual BTS7960 43A Motor Drivers**: High-power H-bridges driving four DC gear motors in differential pair configuration:
  - Left Driver: `RPWM` (Pin 4), `LPWM` (Pin 17), `R_EN` (Pin 23), `L_EN` (Pin 5)
  - Right Driver: `RPWM` (Pin 22), `LPWM` (Pin 21), `R_EN` (Pin 18), `L_EN` (Pin 19)

### Explicit Hardware Realities & Limitations
- **No Wheel Encoders**: The physical rover is **not equipped with wheel encoders**.
- **No IMU**: The physical rover is **not equipped with an IMU** (inertial measurement unit).
- **No Raspberry Pi or Jetson**: There is **no Single Board Computer (SBC)** on board. All computation is handled on the two ESP32 microcontrollers and the connected host PC/laptop.
- **Open-Loop Pose Estimation**: Because there are no wheel encoders or IMU, all pose and position estimation is strictly **open-loop** (calculated via dead-reckoning from commanded velocity, duration, and kinematic approximations).
- **Localization Drift**: **Localization can and will drift over time**. Without encoder odometry, gyro integration, or external SLAM landmarks, global pose is approximate and accumulated positional error is expected.

---

## Quickstart: Current Working Runtime (FastAPI + React)

The primary runtime requires no ROS 2 installation, virtual machine, or Linux operating system. It runs natively on Windows, macOS, or Linux.

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18 or higher with npm
- **Wi-Fi**: A computer with Wi-Fi to connect to the rover's access point

---

### Step 1: Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/crtl-freakssss/ARACHNID.git
   cd ARACHNID
   ```

2. **Configure Python Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate

   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r software/requirements.txt
   ```

3. **Install Frontend Dependencies**:
   ```bash
   cd software/frontend
   npm install
   cd ../..
   ```

---

### Step 2: Connect to Rover Wi-Fi

1. Power on the ARACHNID rover chassis.
2. Brain ESP32 #2 will broadcast a standalone Wi-Fi SoftAP:
   - **SSID**: `ARACHNID`
   - **Password**: `arachnid123`
   - **Target Address**: `192.168.4.1:80`
3. Connect your host machine's Wi-Fi to `ARACHNID`.

---

### Step 3: Launch Mission Control

1. **Start the FastAPI Backend**:
   ```bash
   cd software/backend
   python main.py
   ```
   *The backend starts at `http://localhost:8000` (API docs at `http://localhost:8000/docs`). It automatically establishes the TCP socket to `192.168.4.1:80` when hardware is reachable, or engages the internal kinematic simulator if hardware is offline.*

2. **Start the React Frontend**:
   ```bash
   cd software/frontend
   npm run dev
   ```
   *Open `http://localhost:5173` in any browser to view live sensor telemetry, the 2D occupancy map, directional teleoperation controls, and emergency stop.*

---

## Repository Layout

```
ARACHNID/
├── software/                        # CURRENT WORKING RUNTIME
│   ├── backend/                     # FastAPI server, HardwareGateway, WebSockets, safety manager
│   ├── frontend/                    # React 18 + TypeScript + Vite Mission Control UI
│   ├── config/                      # Hardware configuration profiles
│   └── tests/                       # Backend, frontend, integration & simulation test suite
├── firmware/                        # EMBEDDED FIRMWARE (C++ / Arduino)
│   ├── sensor_esp32/                # Brain ESP32 #2: 5x Ultrasonics, 30°-150° ToF Sweep, SoftAP
│   └── drive_esp32/                 # Rover ESP32 #1: BTS7960 Drivers, 1000ms Watchdog, E-Stop
├── config/                          # Central YAML system configurations
│   ├── robot_config.yaml            # Physical vehicle dimensions & speed limits
│   ├── sensor_config.yaml           # Sensor offsets & filter parameters
│   ├── mapping_config.yaml          # Occupancy grid resolution & parameters
│   ├── navigation_config.yaml       # Path planning & safety stop thresholds
│   └── exploration_config.yaml      # Exploration & frontier parameters
├── docs/                            # In-depth Engineering Documentation
│   ├── DIRECT_WIFI_ARCHITECTURE.md  # Production Wi-Fi architecture specification
│   ├── FINAL_DIRECT_WIFI_AUDIT.md   # Direct Wi-Fi migration audit & verification report
│   ├── HARDWARE_SOFTWARE_GAP_ANALYSIS.md # Hardware reality vs pinout/firmware analysis
│   ├── CONTRACT_V1_0_0.md           # Interface contract & data formats
│   ├── SYSTEM_WORKFLOW.md           # System state transitions & workflows
│   ├── RUN_GUIDE.md                 # Reference run guide
│   └── TESTING_GUIDE.md             # Testing documentation
├── tests/                           # Reference test suite
│   └── contract/                    # Contract schema validation tests
├── ros2_ws/                         # LEGACY / REFERENCE ARCHITECTURE (Preserved in repo)
├── requirements.txt                 # Core Python dependencies
└── README.md                        # Master repository documentation (this file)
```

---

## Legacy / Reference Architecture (`ros2_ws/`)

> [!NOTE]
> **Legacy / Reference Architecture — not required for the current ARACHNID runtime.**

The `ros2_ws/` directory contains an earlier, reference implementation of the autonomy stack built for ROS 2 Humble/Iron (`sensor_interface`, `odometry`, `localization`, `mapping`, `exploration`, `navigation`, and `motor_bridge`). 

**This ROS 2 workspace is not part of the active working runtime.** It is preserved in the repository strictly as reference material, architecture documentation, and for simulated academic experimentation.

If exploring the legacy ROS 2 workspace in a supported Linux environment:
```bash
# Optional reference simulation only (requires ROS 2 Humble):
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build
source install/setup.bash
ros2 launch arachnid_bringup full_system.launch.py mock_mode:=true
```

---

## Testing & Quality Assurance

### Run Current Production Backend Tests
```bash
pytest software/tests -v
```
Verifies the FastAPI backend routes, WebSocket broadcasts, `HardwareGateway`, simulated engine, safety stop logic, and telemetry adapters.

### Run Frontend Typecheck & Build
```bash
cd software/frontend
npm run build
```

### Run Reference Contract Tests
```bash
pytest tests/contract -v
```

---

## Safety Guidelines

> [!WARNING]
> 1. **Elevate the Chassis**: When testing physical drive commands, place the rover on a test stand so wheels do not touch the ground.
> 2. **1000ms Watchdog**: Rover ESP32 #1 actively shuts off motor power if no command is received for 1000ms.
> 3. **Emergency Stop**: The React dashboard provides a prominent emergency stop button that immediately dispatches `STOP\n` down to the hardware bridge.

---

## License

This project is licensed under the MIT License - see the repository LICENSE file for details.
