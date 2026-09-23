# AESAR — Autonomous Exploration & Smart Agricultural Rover

<p align="center">
  <img src="https://img.shields.io/badge/AESAR-Smart%20Agricultural%20Robotics-1a2b5f?style=for-the-badge" alt="AESAR">
  <img src="https://img.shields.io/badge/Autonomy-Enabled-success?style=for-the-badge" alt="Autonomy">
  <img src="https://img.shields.io/badge/Computer%20Vision-Ready-6f42c1?style=for-the-badge" alt="Computer Vision">
  <img src="https://img.shields.io/badge/IoT-Wi--Fi%20Telemetry-009688?style=for-the-badge" alt="IoT">
</p>

<p align="center">
  <b>A modular autonomous agricultural scouting platform for crop exploration, spatial mapping, intelligent observation, and future disease/pest assessment.</b>
</p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-hardware">Hardware</a> •
  <a href="#-aesa-scanning">AESA Scanning</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 🌱 Overview

**AESAR — Autonomous Exploration & Smart Agricultural Rover** is a robotics platform designed to automate crop-field scouting and provide the physical and software infrastructure required for intelligent crop-health monitoring.

The prototype combines:

- 🤖 autonomous rover exploration
- 🧭 navigation and goal-based exploration
- 🗺️ 2D occupancy-grid mapping
- 📡 real-time Wi-Fi telemetry
- 👁️ multi-sensor environmental perception
- 🖥️ browser-based mission control
- 🧠 computer-vision integration points
- 🌿 layer-aware crop observation
- ✈️ a proposed ground–aerial sensing extension for top-canopy analysis

> **Core idea:** agricultural scouting should not be treated as a single-image classification problem. AESAR combines **physical exploration, spatial context, complementary viewpoints, and intelligent analysis**.

---

## 🎯 Objective

Manual crop inspection is repetitive, time-consuming, and dependent on human access to individual plants.

AESAR aims to provide a robotic scouting layer that can:

1. autonomously traverse an agricultural environment,
2. sense and map its surroundings,
3. identify regions requiring observation,
4. capture spatially meaningful crop observations,
5. support computer-vision-based disease/pest assessment, and
6. provide a scalable architecture for future ground–air sensor fusion.

The current prototype therefore focuses on building the **robotic exploration and sensing infrastructure** required before reliable field-scale AI inference can be deployed.

---

## ✨ Novelty & Design Concepts

### 1. Exploration-first agricultural intelligence

AESAR does not assume that the camera is already observing the correct plant.

The system first performs:

```text
Environment
    ↓
Sensor Perception
    ↓
Mapping
    ↓
Exploration
    ↓
Observation Viewpoints
    ↓
Crop Analysis
    ↓
Disease / Pest Assessment
```

This separates **where the robot should go** from **what the vision system should analyze**.

### 2. AESA diagonal scanning

The proposed AESA scanning strategy uses diagonal movement and complementary viewpoints to reduce unnecessary traversal while increasing observation diversity.

```text
START ●
       ╲
        ●
         ╲
          ●
           ╲
            ●
             ╲
              ●
                         → scan direction
```

The navigation layer supplies the trajectory; the agricultural intelligence layer can associate observations with the corresponding spatial locations.

### 3. Layer-aware crop analysis

Crop canopies are three-dimensional. A ground camera can obtain strong lower/middle-canopy observations while the upper canopy may suffer from occlusion or unfavorable viewing angles.

AESAR therefore defines a layer-aware analysis concept:

```text
┌──────────────────────────────┐
│ TOP CANOPY       HIGH PRIORITY│
├──────────────────────────────┤
│ MIDDLE CANOPY                │
├──────────────────────────────┤
│ LOWER CANOPY                 │
└──────────────────────────────┘
               ↓
       Multi-view correlation
               ↓
      Disease / Pest assessment
```

### 4. Ground–aerial sensing extension

A proposed future subsystem adds a UAV that travels in coordination with the rover.

```text
                 ┌───────────────┐
                 │     UAV       │
                 │ Top-canopy    │
                 │ observation   │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │  FUSION LAYER │
                 └───────┬───────┘
                         ▲
                         │
                 ┌───────┴───────┐
                 │     AESAR      │
                 │ Ground Rover   │
                 └───────────────┘
```

The UAV is a **proposed next-stage subsystem**, not part of the currently validated physical rover prototype. Its purpose is to provide complementary top-canopy observations.

---

# 🏗️ Architecture

## Current validated runtime

The primary runtime uses a direct:

**React → FastAPI → Wi-Fi → ESP32 → UART → ESP32 → Motor Driver**

architecture.

```text
┌──────────────────────────────────────────────┐
│             React Mission Control            │
│          Vite + TypeScript + Web UI          │
└──────────────────────┬───────────────────────┘
                       │ HTTP / WebSocket
                       ▼
┌──────────────────────────────────────────────┐
│                FastAPI Backend                │
│                                              │
│ Hardware Gateway • Safety • Telemetry        │
│ Mapping • Navigation • Exploration           │
└──────────────────────┬───────────────────────┘
                       │ Wi-Fi TCP
                       ▼
┌──────────────────────────────────────────────┐
│              Brain ESP32 #2                 │
│  Wi-Fi SoftAP • 5× Ultrasonic • ToF • UART │
└──────────────────────┬───────────────────────┘
                       │ UART 115200
                       ▼
┌──────────────────────────────────────────────┐
│               Rover ESP32 #1                │
│       Motor Control • Watchdog • E-Stop     │
└──────────────────────┬───────────────────────┘
                       ▼
              Dual BTS7960 Drivers
                       ↓
                 4 DC Motors
```

### Runtime data flow

1. Brain ESP32 #2 reads the ultrasonic and ToF sensors.
2. Sensor telemetry is transmitted through the Wi-Fi link.
3. FastAPI receives telemetry and updates system state.
4. Range observations contribute to the 2D occupancy grid.
5. Navigation/exploration generates movement goals.
6. Commands pass through the safety layer.
7. Commands are transmitted to Brain ESP32 #2.
8. Brain ESP32 #2 relays motor commands to Rover ESP32 #1.
9. The React dashboard receives live state through WebSockets.
10. Future crop-analysis modules can consume spatially associated observations.

---

# 🔩 Hardware

AESAR currently uses two ESP32 controllers.

| Controller | Role | Interfaces | Safety |
|---|---|---|---|
| **Brain ESP32 #2** | Sensor acquisition, Wi-Fi, UART bridge | 5× ultrasonic, VL53L0X ToF, servo, UART | Proximity halt |
| **Rover ESP32 #1** | Motor control | Dual BTS7960 H-bridges, 4 DC motors | 1000 ms watchdog + E-stop |

## Sensors

### 5× Ultrasonic

- `us_fc` — Front Center
- `us_fl` — Front Left
- `us_fr` — Front Right
- `us_l` — Left
- `us_r` — Right

### VL53L0X ToF

A servo-mounted VL53L0X performs a forward angular scan approximately across **30°–150°**, providing distance-angle information for spatial mapping.

---

## ⚠️ Known Hardware Limitations

The repository intentionally documents the physical limitations of the current prototype.

The rover currently has:

- **No wheel encoders**
- **No IMU**
- **No Raspberry Pi / Jetson / onboard SBC**
- Open-loop pose estimation
- Expected localization drift over time

Higher-level computation currently runs on the connected host PC/laptop.

These constraints are important when interpreting navigation and localization results and form part of the roadmap for future versions.

---

# 🚀 Quick Start

## Prerequisites

- Python **3.10+**
- Node.js **18+**
- npm
- Wi-Fi adapter
- AESAR rover hardware for physical operation

The software stack can run on Windows, macOS, or Linux.

---

## 1. Clone

```bash
git clone https://github.com/YOUR_USERNAME/AESAR.git
cd AESAR
```

Replace `YOUR_USERNAME` with the account hosting the final repository.

---

## 2. Python environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
pip install -r software/requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install -r software/requirements.txt
```

---

## 3. Frontend

```bash
cd software/frontend
npm install
cd ../..
```

---

## 4. Connect to the rover

Power on the rover and connect the host machine to the rover's Wi-Fi access point.

```text
SSID:       AESAR
IP:         192.168.4.1
TCP Port:   80
```

> **Security:** never commit Wi-Fi passwords, API keys, or other credentials to the public repository. Keep them in local configuration/environment files.

If the current firmware still uses a legacy ARACHNID SSID, update the firmware/configuration before publishing the final repository.

---

## 5. Start FastAPI

```bash
cd software/backend
python main.py
```

Backend:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## 6. Start React

Open another terminal:

```bash
cd software/frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

The dashboard provides:

- live telemetry
- sensor state
- occupancy map
- navigation state
- autonomous exploration
- manual control
- emergency stop

---

## 7. Recommended validation sequence

Before autonomous operation:

```text
Hardware
   ↓
Wi-Fi
   ↓
Backend
   ↓
Frontend
   ↓
Telemetry
   ↓
Manual STOP / motion test
   ↓
Mapping
   ↓
Autonomous exploration
```

### Manual commands

Verify the control path with:

```text
FORWARD
BACKWARD
LEFT
RIGHT
STOP
```

Always verify `STOP` before enabling autonomous motion.

### Autonomous flow

```text
Sensors
   ↓
Mapping
   ↓
Exploration
   ↓
Navigation Goal
   ↓
Safety Manager
   ↓
Motor Command
   ↓
Rover
```

---

# 🗺️ Mapping & Exploration

Range observations are incorporated into a 2D occupancy representation using raycasting.

```text
Sensor
  │
  ▼
Range Measurement
  │
  ▼
Raycasting
  │
  ▼
Occupancy Grid
  │
  ▼
Explored Space
  │
  ▼
Goal / Frontier Selection
  │
  ▼
Navigation
```

The map provides spatial context that can later be used to associate crop observations with locations in the field.

---

# 🌿 AESA Scanning

The agricultural scanning concept builds on the rover's navigation system.

Instead of treating every camera frame as an isolated classification:

```text
Frame 1 → Classify
Frame 2 → Classify
Frame 3 → Classify
```

AESAR moves toward:

```text
Explore
   ↓
Generate observation viewpoints
   ↓
Capture complementary observations
   ↓
Associate with spatial position
   ↓
Separate crop layers
   ↓
Correlate observations
   ↓
Assess crop health
```

This is the conceptual bridge between autonomous robotics and agricultural AI.

---

# 👁️ Crop Analysis Pipeline

```text
        Rover / UAV observation
                  │
                  ▼
          Image acquisition
                  │
                  ▼
        Crop / plant region
             detection
                  │
                  ▼
        Layer-aware analysis
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
       Top      Middle     Lower
        │         │         │
        └─────────┼─────────┘
                  ▼
        Spatial / temporal
             correlation
                  ▼
       Disease / pest signal
                  ▼
          Field assessment
```

The current rover establishes the physical navigation, sensing, mapping, and control foundation for this pipeline.

---

# ✈️ Ground–Aerial Extension

A key design challenge identified during system evaluation is top-canopy visibility.

A future AESAR architecture can use an aerial subsystem to complement the ground rover:

```text
                  UAV
                   │
                   ▼
             TOP CANOPY
                   │
                   │
                   ▼
             ┌─────────┐
             │ FUSION  │
             │ ENGINE  │
             └────┬────┘
                  ▲
                  │
             GROUND ROVER
                  │
                  ▼
          LOWER / MIDDLE CANOPY
```

An event-triggered architecture is also possible:

```text
Rover exploration
       ↓
Potential anomaly
       ↓
Top-layer verification required?
       ↓
      YES
       ↓
UAV observation
       ↓
Ground + aerial correlation
       ↓
Final assessment
```

This avoids assuming that the UAV must operate continuously and creates a path toward energy-aware multi-agent scouting.

---

# 🧪 Testing

### Backend

```bash
pytest software/tests -v
```

### Frontend build

```bash
cd software/frontend
npm run build
```

### Contract tests

```bash
pytest tests/contract -v
```

---

# 🛡️ Safety

> [!WARNING]
> Physical robotics can cause injury or equipment damage. Test carefully.

1. Elevate the chassis during initial motor tests.
2. Keep hands and loose wires away from moving components.
3. Verify the emergency stop before autonomous operation.
4. Start at low speed.
5. Test one movement command at a time.
6. Confirm the watchdog is active.

The drive ESP32 uses a **1000 ms communication timeout watchdog** to stop motor output when commands are lost.

---

# 📁 Repository Structure

```text
AESAR/
├── software/
│   ├── backend/             # FastAPI runtime
│   ├── frontend/            # React + TypeScript mission control
│   ├── config/              # Software configuration
│   └── tests/               # Runtime tests
│
├── firmware/
│   ├── sensor_esp32/        # Sensor / Wi-Fi controller
│   └── drive_esp32/         # Motor controller
│
├── config/
│   ├── robot_config.yaml
│   ├── sensor_config.yaml
│   ├── mapping_config.yaml
│   ├── navigation_config.yaml
│   └── exploration_config.yaml
│
├── docs/
│   ├── DIRECT_WIFI_ARCHITECTURE.md
│   ├── FINAL_DIRECT_WIFI_AUDIT.md
│   ├── HARDWARE_SOFTWARE_GAP_ANALYSIS.md
│   ├── CONTRACT_V1_0_0.md
│   ├── SYSTEM_WORKFLOW.md
│   ├── RUN_GUIDE.md
│   └── TESTING_GUIDE.md
│
├── tests/
│   └── contract/
│
├── ros2_ws/                 # Legacy / reference architecture
├── requirements.txt
├── LICENSE
└── README.md
```

---

# 📚 Documentation Map

For reviewers and developers, the recommended reading order is:

1. [`RUN_GUIDE.md`](docs/RUN_GUIDE.md) — run the system
2. [`SYSTEM_WORKFLOW.md`](docs/SYSTEM_WORKFLOW.md) — understand execution flow
3. [`DIRECT_WIFI_ARCHITECTURE.md`](docs/DIRECT_WIFI_ARCHITECTURE.md) — understand communication
4. [`HARDWARE_SOFTWARE_GAP_ANALYSIS.md`](docs/HARDWARE_SOFTWARE_GAP_ANALYSIS.md) — understand hardware realities
5. [`CONTRACT_V1_0_0.md`](docs/CONTRACT_V1_0_0.md) — interfaces and data formats
6. [`TESTING_GUIDE.md`](docs/TESTING_GUIDE.md) — validation

---

# 🕰️ ROS 2 Reference Architecture

`ros2_ws/` contains an earlier ROS 2 architecture and is preserved as reference material.

It is **not required by the current production runtime**.

Current validated architecture:

```text
React
  ↕
FastAPI
  ↕
Wi-Fi TCP
  ↕
ESP32 #2
  ↕
UART
  ↕
ESP32 #1
  ↕
Motor Drivers
```

---

# 🗺️ Roadmap

## ✅ Prototype foundation

- [x] Dual-ESP32 rover
- [x] Wi-Fi telemetry
- [x] UART motor-control bridge
- [x] Differential drive
- [x] Ultrasonic perception
- [x] Servo-mounted ToF scanning
- [x] 2D occupancy mapping
- [x] Safety manager
- [x] Motor watchdog
- [x] React mission-control dashboard
- [x] Autonomous exploration foundation

## 🔄 Next engineering stage

- [ ] Integrate crop-specific computer vision
- [ ] Associate crop observations with map coordinates
- [ ] Implement layer-aware crop observations
- [ ] Correlate observations across viewpoints
- [ ] Add encoder/IMU-assisted localization
- [ ] Experimentally validate AESA diagonal scanning

## 🚀 Future research

- [ ] Event-triggered UAV deployment
- [ ] Ground–aerial sensor fusion
- [ ] Top-canopy verification
- [ ] Field-scale crop-health mapping
- [ ] Disease/pest confidence estimation
- [ ] Multi-agent agricultural scouting
- [ ] Edge inference optimization

---

# 🎥 Demo & Media

Add project media under:

```text
docs/media/
├── aesar-overview.png
├── rover.jpg
├── mission-control.png
├── autonomous-exploration.gif
├── aesa-scan.gif
└── architecture.png
```

Embed images directly:

```markdown
![AESAR Mission Control](docs/media/mission-control.png)
```

Embed the project demonstration:

```markdown
[▶️ Watch the AESAR autonomous exploration demo](YOUR_VIDEO_URL)
```

---

# 🔗 Project Links

- **GitHub:** `https://github.com/YOUR_USERNAME/AESAR`
- **Demo Video:** `YOUR_VIDEO_URL`
- **Presentation:** `YOUR_PRESENTATION_URL`
- **LinkedIn Showcase:** `YOUR_LINKEDIN_POST_URL`
- **Documentation:** [`docs/`](docs/)

Replace placeholders before publishing.

---

# 👥 Team

| Contributor | Area |
|---|---|
| Name | Robotics / Embedded |
| Name | Computer Vision |
| Name | Backend / Frontend |
| Name | AI / Research |

---

# 📜 License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).

---

<p align="center">
  <b>AESAR</b><br>
  Autonomous Exploration • Smart Agriculture • Intelligent Sensing
</p>

<p align="center">
  Built as a robotics research prototype for autonomous agricultural scouting.
</p>
