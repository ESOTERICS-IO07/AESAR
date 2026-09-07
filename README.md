# AESAR

**Autonomous Ecological Scouting & Adaptive Response Rover**

AESAR is an agricultural intelligence and autonomous scouting system implemented on top of the existing ARACHNID autonomous rover platform. It focuses on Non-Pesticidal Management (NPM) through edge-AI biological pest-to-defender quantification and spatial microclimate intelligence.

## Relationship with ARACHNID

- **ARACHNID**: The mobility and spatial subsystem. It provides the base rover, motor control, obstacle avoidance, and basic autonomous navigation.
- **AESAR**: The agricultural and ecological intelligence subsystem. It adds vision, pest/defender detection, ecosystem assessment, and mission control. 

## High-Level Architecture

```text
Sensors -> Brain ESP32 -> Hardware Gateway -> Normalized Telemetry 
-> [Localization | Vision | Environment] 
-> Station Analysis -> PDR + AMRI -> AESA Decision 
-> Field Card / Action -> Mission Controller 
-> Existing ARACHNID Navigation -> Drive ESP32 -> Motors
```

### Important Architecture Restrictions
- Mission/AI modules must **NOT** directly control motor GPIOs.
- The existing Drive ESP32 remains the motor authority.
- AESAR should issue high-level navigation requests through the integration layer.

## Current Hardware

**ARACHNID (Existing):**
- Dual ESP32 Architecture: Brain/Sensor ESP32 and Drive/Motor ESP32
- 5 ultrasonic sensors
- VL53L0X ToF with servo sweep
- Dual BTS7960 motor drivers

**AESAR Additions:**
- MPU6050 (Heading integration)
- Camera (Vision integration)
- Environmental sensors

## Team Ownership

- **Person 1**: Hardware + Integration (`feature/hardware-integration`)
- **Person 2**: Vision / AI (`feature/vision-ai`)
- **Person 3**: Ecosystem Intelligence (`feature/ecosystem-intelligence`)
- **Person 4**: Mission + Dashboard (`feature/mission-dashboard`)

## Repository Structure

```
AESAR/
├── backend/app/    # Core logic (Hardware, localization, vision, ecosystem, decision, mission, etc.)
├── data/mock/      # Mock JSON data for decoupled development
├── docs/           # Documentation (Architecture, Hardware, Interfaces, Development workflow)
├── firmware/brain/ # ESP32 Firmware
├── frontend/       # Dashboard and UI
├── models/         # AI Models (YOLO, etc.)
├── scripts/        # Utility scripts
└── tests/          # Test suites
```

## Development Workflow

1. All feature work happens in dedicated `feature/*` branches.
2. PRs are submitted targeting the `integration` branch.
3. The `integration` branch is tested before merging into `main`.
4. `main` represents the stable, demo-ready state of AESAR.

### Creating a Feature Branch

1. Clone the repository and fetch updates:
   ```bash
   git clone <REPOSITORY_URL>
   cd AESAR
   git fetch origin
   git checkout integration
   git pull origin integration
   ```
2. Create and push your feature branch (NEVER branch off someone else's feature branch):
   ```bash
   git checkout -b feature/<your-feature-name>
   git push -u origin feature/<your-feature-name>
   ```

### Submitting a PR

- Submit PRs against the `integration` branch.
- PR descriptions must include: what changed, files changed, interface changes, testing performed, and integration impact.
- Avoid giant PRs.
- If an interface changes, update `docs/INTERFACES.md` and inform Person 1.

## Implementation Status

- [IMPLEMENTED] Initial Repository Setup & Git Workflow
- [IMPLEMENTED] Mock Data Generation
- [PLANNED] Hardware Integration (MPU6050, Camera)
- [PLANNED] YOLO Inference Pipeline
- [PLANNED] AMRI & PDR Calculation
- [PLANNED] 10-Station Scouting Mission
