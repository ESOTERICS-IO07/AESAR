# AESAR MASTER IMPLEMENTATION CONTRACT
## Autonomous Ecosystem Scouting & Analysis Rover for Non-Pesticidal Management
### Team Engineering Contract v2.1 — Hackathon Source of Truth

**Repository:** `AESAR`  
**Base platform:** Existing working ARACHNID autonomous rover  
**Status:** TEAM SOURCE OF TRUTH

> **No-assumption rule:** If a value, pin, protocol, threshold, coefficient, sensor, API field, state, or behavior is not explicitly defined in this contract or an authoritative referenced project document, it must not be invented. Mark it `TBD`, document the gap, and notify the integration owner.

---

# 1. AUTHORITY AND SOURCE OF TRUTH

This contract consolidates the current AESAR implementation baseline from the project's AESAR technical specification, actual hardware/communication audit, direct-Wi-Fi architecture, and ARACHNID integration documents.

## 1.1 Authority order

When sources conflict, use this order:

1. Actual tested hardware/firmware and latest direct-Wi-Fi hardware audit.
2. This contract.
3. AESAR research paper / Master Implementation Contract v2.0.0.
4. ARACHNID direct-Wi-Fi architecture.
5. Older ARACHNID ROS2 documents.
6. General engineering assumptions are not authoritative.

Older ROS2 documents are historical/reference material where they conflict with the direct-Wi-Fi implementation.

## 1.2 Prohibited assumptions

Do not assume:
- wheel encoders exist;
- ROS2 is in the physical path;
- the current Drive ESP32 accepts JSON velocity commands;
- the ToF is fixed rather than servo-scanned;
- frontend can communicate directly with ESP32;
- a sensor exists merely because an old document mentions it;
- a GPIO is available without hardware verification;
- an undocumented PDR/AMRI weight or threshold;
- simulated navigation equals physically validated navigation;
- MPU6050 provides accurate global X/Y localization;
- a model is trained or accurate unless actually tested.

---

# 2. PROJECT DEFINITION

AESAR automates a 10-plant diagonal CESA/AESA-style ecological scouting workflow for Non-Pesticidal Management.

The system combines:
- ground-level under-canopy sensing;
- multi-angle plant imaging;
- pest/defender detection;
- soil and microclimate measurements;
- Pest-to-Defender Ratio (PDR);
- Abiotic Microclimate Risk Index (AMRI);
- AESA/NPM decision logic;
- station field cards;
- mapping and telemetry;
- mission orchestration.

## 2.1 ARACHNID baseline

ARACHNID supplies:
- four-wheel differential-drive rover;
- dual ESP32 controllers;
- motors and dual BTS7960 drivers;
- 5 ultrasonic channels;
- VL53L0X ToF;
- servo-mounted ToF scan;
- existing mapping/navigation;
- Wi-Fi/TCP;
- tested low-level movement.

## 2.2 AESAR additions

AESAR adds:
- MPU6050 heading assistance;
- agricultural/environmental sensing;
- camera interface;
- YOLO vision;
- pest/defender classification;
- PDR;
- AMRI;
- AESA decision engine;
- NPM recommendation;
- field cards;
- 10-station mission;
- ecological/semantic presentation.

---

# 3. SYSTEM ARCHITECTURE

```text
                         AESAR
                           |
        +------------------+------------------+
        |                  |                  |
   HARDWARE             INTELLIGENCE       DASHBOARD
        |                  |                  |
 Brain ESP32          FastAPI/Python      React/TS
 Rover ESP32          Vision              WebSocket
 Sensors              PDR/AMRI           REST
 Motors               AESA               Map/UI
                      Mission
        |                  |
        +---------> Hardware Gateway
                           |
                     Existing Rover
                      Navigation
                           |
                       Motors
```

## 3.1 Layer 1 — Embedded

Execution:
- Brain ESP32 #2;
- Rover ESP32 #1;
- physical sensors/actuators.

## 3.2 Layer 2 — Autonomy and AESA intelligence

Execution:
- laptop/edge computer;
- Python 3.10+;
- FastAPI.

## 3.3 Layer 3 — Dashboard

Execution:
- browser;
- React 18 + TypeScript + Vite.

**Browser connects only to backend.**

---

# 4. HARDWARE CONTRACT

## 4.1 Brain ESP32

Known tested/current functions:

| GPIO | Function |
|---|---|
| 19 | UART TX → Rover RX |
| 18 | UART RX ← Rover TX |
| 14 | ToF servo |
| 21 | VL53L0X SDA |
| 22 | VL53L0X SCL |
| 25 | Ultrasonic shared TRIG |
| 32 | Front-center ultrasonic ECHO |
| 27 | 45°-left ultrasonic ECHO |
| 35 | 45°-right ultrasonic ECHO |
| 34 | Left ultrasonic ECHO |
| 33 | Right ultrasonic ECHO |

MPU6050:
- SDA → GPIO21;
- SCL → GPIO22;
- 3.3V;
- GND;
- shares I2C with VL53L0X.

Any additional agricultural sensor pin allocation must be verified against the physical assembly before use.

## 4.2 Rover ESP32

| GPIO | Function |
|---|---|
| 4 | Left BTS7960 RPWM |
| 17 | Left BTS7960 LPWM |
| 23 | Left R_EN |
| 5 | Left L_EN |
| 22 | Right BTS7960 RPWM |
| 21 | Right BTS7960 LPWM |
| 18 | Right R_EN |
| 19 | Right L_EN |
| 26 | UART RX ← Brain TX |
| 25 | UART TX → Brain RX |

Preserve the tested motor polarity/direction mapping.

## 4.3 UART

Brain ↔ Rover:
- 115200 baud;
- 8 data bits;
- no parity;
- 1 stop bit.

## 4.4 Motor protocol

Current physical command protocol:

```text
FORWARD\n
BACKWARD\n
LEFT\n
RIGHT\n
STOP\n
```

The current integration must not send JSON motor packets.

Do not send JSON and ASCII motor commands back-to-back.

A future velocity protocol is outside the initial critical path.

---

# 5. NETWORK CONTRACT

Current tested Brain network:
- SSID: `ARACHNID`;
- password: `arachnid123`;
- IP: `192.168.4.1`;
- TCP port: `80`.

The AESAR specification contains `AESAR_ROVER` in some sections, but the tested firmware/audit baseline is authoritative for the physical demo.

## 5.1 Data direction

```text
Sensors
  ↓
Brain ESP32
  ↓ TCP
FastAPI Hardware Gateway
  ↓
Normalized backend events
  ↓ WebSocket
React

React / Mission
  ↓
FastAPI
  ↓ TCP
Brain
  ↓ UART
Rover ESP32
  ↓
BTS7960
  ↓
Motors
```

---

# 6. TELEMETRY CONTRACT

## 6.1 Canonical logical telemetry

```json
{
  "type": "sensor_telemetry",
  "timestamp_ms": 123456789,
  "seq": 42,
  "ultrasonic": {
    "front_mm": 420,
    "front_left_mm": 510,
    "front_right_mm": 490,
    "left_mm": 1200,
    "right_mm": 1150
  },
  "tof_scan": {
    "angle_deg": 118,
    "distance_mm": 380
  },
  "imu": {
    "accel_x_mps2": 0.0,
    "accel_y_mps2": 0.0,
    "accel_z_mps2": 9.81,
    "gyro_x_rads": 0.0,
    "gyro_y_rads": 0.0,
    "gyro_z_rads": 0.0,
    "yaw_deg": 0.0
  },
  "abiotic_sensors": {
    "soil_moisture_percent": null,
    "canopy_temp_c": null,
    "relative_humidity_percent": null
  },
  "hardware_status": {
    "brain_wifi_rssi": null,
    "rover_uart_connected": true,
    "safety_stop_latched": false
  }
}
```

Fields not physically implemented must not be fabricated.

## 6.2 Units

Hardware:
- range = millimetres;
- acceleration = m/s²;
- angular velocity = rad/s.

Software:
- position = metres;
- navigation yaw = radians;
- linear velocity = m/s;
- angular velocity = rad/s.

UI may display degrees for human readability.

## 6.3 Invalid values

The old firmware may use `999` as an invalid/disconnected range sentinel.

Normalized software representation:

```text
-1 = invalid/unavailable
```

Never interpret invalid range data as clear space.

---

# 7. TOF CONTRACT

Hardware:
- VL53L0X;
- servo-mounted;
- expected scan range approximately 30°–150°;
- expected step approximately 2°.

Logical sample:

```json
{
  "angle_deg": 118,
  "distance_mm": 380
}
```

The backend must preserve both angle and distance.

A fixed `tof_front_mm`-only abstraction is insufficient for the scanning architecture.

---

# 8. MPU6050 CONTRACT

## 8.1 Purpose

The MPU6050 is primarily used for:
- heading assistance;
- turn completion;
- orientation estimation.

It is not a guarantee of:
- accurate global X/Y;
- full inertial navigation;
- full SLAM;
- encoder-equivalent odometry.

## 8.2 Initial behavior

Brain:
1. initialize MPU6050;
2. read accelerometer and gyro;
3. calibrate gyro bias while stationary;
4. integrate gyro Z for heading assistance;
5. expose telemetry.

Backend:
- validate health;
- track staleness;
- use heading for orientation/turn assistance.

## 8.3 Prohibited

Do not double-integrate accelerometer readings and claim accurate position.

## 8.4 Encoders

Wheel encoders are not present in the current physical baseline.

Do not create encoder-dependent functionality that pretends encoder telemetry exists.

Future scope may add wheel encoders and RTK-GPS.

---

# 9. LOCALIZATION AND MAPPING

Coordinate frame:

```text
+X = forward
+Y = left
+Z = up
```

Yaw:
- counter-clockwise from +X;
- normalized to [-π, π];
- radians internally.

Existing occupancy grid:
- 200 × 200 cells;
- 0.05 m/cell;
- origin approximately [-5.0 m, -5.0 m];
- free = 0;
- occupied = 100;
- unknown = -1;
- Bresenham-style raycasting.

For a stationary rover:

```text
x = distance_m × cos(angle_rad)
y = distance_m × sin(angle_rad)
```

For moving global mapping, valid pose is required.

Do not claim globally accurate persistent SLAM without a validated pose source.

---

# 10. NAVIGATION AUTHORITY

## 10.1 Absolute rule

Only one layer may control movement at any moment.

## 10.2 Initial prototype

The existing ARACHNID movement/navigation behavior remains the physical low-level authority where required by the tested platform.

AESAR mission logic requests high-level station movement.

It must not directly manipulate motors.

## 10.3 Forbidden paths

```text
Vision → Motors
AESA → Motors
Frontend → Motors
Mission FSM → Motor GPIO
```

Correct pattern:

```text
Mission
  ↓
High-level navigation request
  ↓
Integration layer
  ↓
Existing ARACHNID navigation/control
  ↓
Drive ESP32
  ↓
Motors
```

---

# 11. SAFETY CONTRACT

## 11.1 Hardware watchdog

Rover ESP32 watchdog:
- timeout = 1000 ms;
- loss of valid UART commands → motor stop.

Do not disable it.

## 11.2 Obstacle stop

AESAR specification baseline:
- safety distance = 180 mm / 0.18 m.

Any physical change must be tested and documented.

## 11.3 E-stop

The backend/frontend E-stop:
- sends `STOP`;
- latches emergency state;
- prevents normal motion until reset.

## 11.4 Communication loss

Brain must stop the actuator path when its controlling connection is lost.

Backend must also issue STOP on applicable failure/disconnect paths.

## 11.5 Safety precedence

```text
E-STOP / SAFETY
       >
MISSION
       >
NAVIGATION
       >
NORMAL MOTION
```

Safety must never wait for:
- YOLO;
- PDR;
- AMRI;
- UI rendering.

---

# 12. MISSION STATE MACHINE

Canonical high-level lifecycle:

```text
IDLE
 ↓
PLAN_MISSION
 ↓
GO_TO_STATION
 ↓
ARRIVED
 ↓
CAPTURE
 ↓
YOLO
 ↓
ABIOTIC_SAMPLE
 ↓
PDR_AMRI
 ↓
FIELD_CARD
 ↓
NEXT_STATION
 ↓
GO_TO_STATION
 ...
 ↓
COMPLETE
```

The source AESAR specification expresses the same lifecycle as:
- standby/diagnostics;
- row following;
- station detection;
- dwell/capture;
- YOLO;
- abiotic sampling;
- increment station;
- final field card after station 10.

## 12.1 Mission size

Exactly:
```text
10 representative stations
```

Stations:
```text
1 ... 10
```

## 12.2 Canopy views

Target:
- lower;
- middle;
- upper.

If a view cannot be captured, mark it unavailable. Do not fabricate it.

## 12.3 Station completion

A station is complete only after:
- arrival/dwell;
- required image attempts;
- vision result or explicit failure;
- abiotic sample or explicit unavailable status;
- station record.

---

# 13. PERSON 2 — VISION/AI CONTRACT

Branch:
```text
feature/vision-ai
```

Owns:
- camera abstraction;
- image capture;
- preprocessing;
- YOLO;
- pest detection;
- defender detection;
- vision result schema;
- tests;
- mock images.

Pest classes specified:
- Brown Planthopper (BPH);
- Green Leafhopper (GLH);
- Yellow Stem Borer;
- Cotton Aphids;
- Chilli Thrips;
- American Bollworm.

Defender classes:
- Ladybird Beetle adult/larva;
- Lycosa/Wolf Spider;
- Mirid Bug;
- Carabid Beetle;
- Green Lacewing.

## 13.1 Vision result

```json
{
  "station_id": 3,
  "view": "upper",
  "detections": [
    {
      "class": "aphid",
      "category": "pest",
      "confidence": 0.91,
      "count": 1
    }
  ]
}
```

Do not claim a model accuracy or training dataset result unless the team actually validates it.

---

# 14. PERSON 3 — PDR/AMRI/AESA CONTRACT

Branch:
```text
feature/ecosystem-intelligence
```

## 14.1 PDR

```text
PDR =
Σ(wp,j × Npest,i,j)
/
(Σ(wd,k × Ndefender,i,k) + ε)
```

where:
- `Npest,i,j` = pest count;
- `wp,j` = pest voracity weight;
- `Ndefender,i,k` = defender count;
- `wd,k` = defender predation weight;
- `ε = 10^-3`.

If species-specific weights are not explicitly provided, they are `TBD`.

Do not invent them.

## 14.2 AMRI

```text
AMRI_i =
0.35 × ((Tcanopy,i - Topt) / Topt)^2
+
0.40 × (RHambient,i / 100)
+
0.25 × (1 - Msoil,i / Mfield_cap)
```

Variables:
- `Tcanopy` = canopy temperature;
- `Topt` = optimum temperature;
- `RHambient` = relative humidity percentage;
- `Msoil` = soil moisture;
- `Mfield_cap` = field soil capacity.

If crop-specific `Topt` or `Mfield_cap` is not provided, configuration is required before claiming a calibrated AMRI.

---

# 15. NPM DECISION MATRIX

| Condition | Ecosystem state | Chemical recommendation | NPM intervention |
|---|---|---|---|
| PDR ≤ 1.0 AND AMRI < 0.50 | Perfect Ecological Balance | STRICTLY FORBIDDEN (0% spray) | Natural biological control; no intervention required |
| 1.0 < PDR ≤ 2.5 AND AMRI < 0.65 | Moderate Pest Buildup | NO SYNTHETIC CHEMICALS | Yellow/blue sticky traps; Trichogramma egg parasitoids; NSKE 5% |
| PDR > 2.5 OR AMRI ≥ 0.80 | Ecological Imbalance | Non-Pesticidal Corrective Focus | Bird perches; botanical bio-extracts; irrigation adjustment; re-survey in 72 h |

## 15.1 Undefined decision region

The supplied matrix does not explicitly define every combination between:
- AMRI 0.65 and 0.80;
- PDR > 1.0 with AMRI ≥ 0.65 and < 0.80.

Therefore the engine must return:

```text
UNSPECIFIED / REVIEW_REQUIRED
```

unless the team formally adds a documented rule.

---

# 16. FIELD CARD CONTRACT

A station field card may contain:

- station ID;
- coordinates;
- view status;
- pest detections;
- defender detections;
- counts;
- PDR;
- soil moisture;
- canopy temperature;
- relative humidity;
- AMRI;
- ecosystem state;
- recommendation;
- timestamp;
- data-quality/confidence information.

No card may claim a measurement that was not actually obtained.

---

# 17. PERSON 4 — MISSION/DASHBOARD CONTRACT

Branch:
```text
feature/mission-dashboard
```

Owns:
- mission FSM;
- station manager;
- 10-station lifecycle;
- mission status;
- dashboard;
- live telemetry visualization;
- station UI;
- field card UI.

Mission module must communicate through high-level contracts.

It must not:
- access GPIO;
- access ESP32 directly;
- issue raw motor commands.

---

# 18. PERSON 1 — HARDWARE/INTEGRATION CONTRACT

Branch:
```text
feature/hardware-integration
```

Owns:
- Brain ESP32;
- MPU6050;
- ToF/servo;
- ultrasonic integration;
- agricultural sensor hardware;
- camera hardware connection;
- hardware gateway;
- telemetry normalization;
- localization/heading;
- mapping integration;
- safety;
- ARACHNID integration;
- final end-to-end physical testing.

Person 1 is final integration owner.

---

# 19. FILE OWNERSHIP

```text
firmware/brain/               Person 1
backend/app/hardware/         Person 1
backend/app/localization/     Person 1
backend/app/safety/           Person 1
backend/app/mapping/          Person 1 + Person 4

backend/app/vision/           Person 2
backend/app/ecosystem/        Person 3
backend/app/decision/         Person 3
backend/app/mission/          Person 4

frontend/                     Person 4
backend/app/models/           Shared / integration reviewed
docs/                         Shared / integration reviewed
tests/                        Subsystem owner
data/mock/                    Shared
```

---

# 20. GIT CONTRACT

Branch structure:

```text
main
 |
 └── integration
      |
      ├── feature/hardware-integration
      ├── feature/vision-ai
      ├── feature/ecosystem-intelligence
      └── feature/mission-dashboard
```

Rules:
- no direct push to `main`;
- feature branches originate from `integration`;
- PRs target `integration`;
- `integration` is tested;
- only stable/demo-ready code reaches `main`;
- never branch from another person's feature branch.

Commands:

```bash
git clone <REPOSITORY_URL>
cd AESAR
git fetch origin
git checkout integration
git pull origin integration
```

Person 2:
```bash
git checkout -b feature/vision-ai
git push -u origin feature/vision-ai
```

Person 3:
```bash
git checkout -b feature/ecosystem-intelligence
git push -u origin feature/ecosystem-intelligence
```

Person 4:
```bash
git checkout -b feature/mission-dashboard
git push -u origin feature/mission-dashboard
```

Feature workflow:

```text
feature
  ↓
commit
  ↓
push
  ↓
Pull Request
  ↓
integration
  ↓
test
  ↓
main
```

Recommended commit prefixes:
```text
feat:
fix:
docs:
refactor:
test:
chore:
```

---

# 21. INTERFACE CHANGE CONTROL

Any change to:
- JSON fields;
- units;
- enum/state names;
- REST endpoints;
- WebSocket events;
- command format;
- required/optional fields;
- safety thresholds;
- coordinate convention

must update the relevant documentation and notify Person 1.

No silent interface changes.

---

# 22. MOCK-FIRST DEVELOPMENT

Required:

```text
data/mock/
├── telemetry.json
├── detections.json
├── ecosystem.json
└── mission.json
```

Mock data must use the same logical contracts as real data.

Teammates must be able to develop without physical rover access.

---

# 23. FRONTEND CONTRACT

Frontend communicates only with FastAPI.

Frontend must not:
- parse raw ESP32 packets;
- translate motor commands;
- perform hardware coordinate transforms;
- implement hardware safety;
- connect directly to ESP32.

Existing map components should be reused where possible.

---

# 24. EXPECTED EVENTS

The normalized backend may expose:

```text
sensor_telemetry
rover_status
map_update
navigation_update
exploration_update
tof_scan
aesa_transect_packet
field_card
```

Exact final schemas must be documented before integration.

---

# 25. TEST CONTRACT

Minimum physical tests:

1. Brain/backend connection.
2. ToF sweep.
3. Five ultrasonic telemetry.
4. MPU6050 heading.
5. Manual FORWARD/BACKWARD/LEFT/RIGHT/STOP.
6. Rover watchdog.
7. Obstacle stop.
8. Wi-Fi/TCP loss stop.
9. Stationary mapping.
10. End-to-end mission.

Software tests:

### Vision
- empty detections;
- multiple detections;
- confidence;
- schema validation;
- unavailable image.

### PDR
- zero pests;
- zero defenders;
- multiple species;
- epsilon;
- missing data.

### AMRI
- normal values;
- boundaries;
- missing values;
- crop configuration.

### Decision engine
- every defined boundary;
- undefined decision region;
- no silent recommendation.

### Mission
- mission start;
- station 1;
- station 10;
- capture failure;
- vision failure;
- sensor failure;
- safety stop;
- completion;
- reset.

### Frontend
- connection;
- telemetry;
- mission progress;
- station result;
- field card;
- E-stop;
- stale data.

---

# 26. END-TO-END ACCEPTANCE

```text
START
 ↓
Diagnostics
 ↓
Plan 10 stations
 ↓
Navigate
 ↓
Arrive
 ↓
Capture lower/middle/upper
 ↓
YOLO
 ↓
Abiotic sample
 ↓
PDR + AMRI
 ↓
AESA decision
 ↓
Field card
 ↓
Next station
 ↓
...
 ↓
Station 10
 ↓
Final field card
 ↓
COMPLETE
```

The demo must visibly establish:
- rover movement;
- obstacle safety;
- sensor telemetry;
- station progress;
- vision output;
- PDR;
- AMRI;
- recommendation;
- field card;
- mapping/position information only to the level physically justified.

---

# 27. DEMO CHECKLIST

Before autonomous movement:

1. power/battery;
2. motor wiring;
3. wheel/mechanical inspection;
4. Brain power;
5. Rover power;
6. UART;
7. Wi-Fi;
8. telemetry;
9. E-stop;
10. watchdog;
11. obstacle stop;
12. camera;
13. mission reset;
14. one-station test;
15. multi-station test;
16. full mission.

Do not debug new firmware while the rover is moving.

---

# 28. OUT OF SCOPE FOR THE INITIAL HACKATHON

Do not make these critical-path dependencies:

- wheel encoder installation;
- RTK-GPS;
- full visual SLAM;
- full inertial dead reckoning;
- ROS2 migration;
- Nav2 migration;
- Drive ESP32 replacement;
- new velocity motor protocol;
- chassis redesign;
- chemical spraying hardware;
- multispectral sensing.

These are future extensions unless formally added by contract revision.

---

# 29. KNOWN LIMITATIONS

Because the current physical platform lacks wheel encoders:
- global position can drift;
- MPU6050 improves heading but does not guarantee accurate X/Y;
- mapping quality depends on pose quality;
- prototype station coordinates may be approximate.

The team must not claim more than has been physically validated.

---

# 30. DEFINITION OF DONE

A subsystem is complete only when:

- interface is documented;
- tests exist;
- mock data works;
- errors are handled;
- missing data is explicit;
- unrelated subsystems remain functional;
- feature branch is pushed;
- PR is created;
- integration impact is documented;
- integration checks pass.

---

# 31. FINAL NON-NEGOTIABLE RULES

1. **Do not assume.**
2. **Do not silently change interfaces.**
3. **Do not bypass safety.**
4. **Only one movement authority at a time.**
5. **Current motor protocol is ASCII, not JSON.**
6. **Wheel encoders are not present.**
7. **MPU6050 is heading assistance, not full SLAM.**
8. **Browser never connects directly to ESP32.**
9. **Feature branches never push directly to main.**
10. **Unknown values become TBD, not invented values.**

---

# 32. QUICK REFERENCE

```text
REPOSITORY
AESAR

TEAM
P1 = Hardware + Integration
P2 = Vision / AI
P3 = PDR + AMRI + AESA
P4 = Mission + Dashboard

BRANCHES
main
integration
feature/hardware-integration
feature/vision-ai
feature/ecosystem-intelligence
feature/mission-dashboard

CONTROLLERS
Brain ESP32 #2
Rover ESP32 #1

BRAIN → BACKEND
TCP :80
JSON telemetry

BRAIN → ROVER
UART 115200
ASCII commands

COMMANDS
FORWARD
BACKWARD
LEFT
RIGHT
STOP

WATCHDOG
1000 ms

OBSTACLE BASELINE
180 mm

TOF
VL53L0X
Servo
30°–150°
~2° steps

I2C
SDA 21
SCL 22

MPU6050
Heading assistance

ENCODERS
NOT PRESENT

MAP
200×200
0.05 m/cell
0 free
100 occupied
-1 unknown

MISSION
10 stations

VIEWS
LOWER / MIDDLE / UPPER

PDR EPSILON
10^-3

AMRI
α=0.35
β=0.40
γ=0.25

FINAL INTEGRATION OWNER
Person 1
```

**END OF AESAR MASTER IMPLEMENTATION CONTRACT v2.1**
