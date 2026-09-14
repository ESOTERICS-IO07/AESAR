# Direct Wi-Fi Architecture (ROS 2 Removed)

This document outlines the final architecture for the ARACHNID project, which has completely eliminated ROS 2 and Ubuntu dependencies in favor of a direct Python-to-ESP32 Wi-Fi architecture.

## Overview

The system is now a two-tier architecture:
1. **Frontend**: React/TypeScript client for visualization and teleoperation.
2. **Backend**: A pure Python FastAPI server running on any standard OS (Windows/Linux/Mac). 

The backend communicates *directly* with the physical hardware via a TCP socket connected to the Brain ESP32's SoftAP Wi-Fi network (`192.168.4.1:80`).

## Hardware Diagram

```
                    HARDWARE
                       │
              ┌────────┴────────┐
              │                 │
        5 Ultrasonics       ToF + Servo
              │                 │
              └────────┬────────┘
                       ↓
                  BRAIN ESP32
                       │
                      Wi-Fi (TCP 192.168.4.1:80)
                       │
                       ↓
                 PYTHON BACKEND (FastAPI)
                       │
                ┌──────┴──────┐
                ↓             ↓
             Mapping      Navigation
                │             │
                └──────┬──────┘
                       ↓
                 Motor command (ASCII)
                       │
                      Wi-Fi
                       ↓
                  BRAIN ESP32
                       │
                      UART (115200 baud)
                       ↓
                  ROVER ESP32
                       │
                    BTS7960
                       │
                     Motors
```

## Data Protocols

### Brain ESP32 → Backend (Telemetry)
The Brain ESP32 continuously transmits JSON payloads containing sensor data over the TCP socket. The backend parses this without any ROS 2 middleware.

**Canonical Format**:
```json
{
  "type": "sensor_telemetry",
  "timestamp_ms": 123456,
  "seq": 42,
  "us_fc_mm": 450,
  "us_fl_mm": 600,
  "us_fr_mm": 550,
  "us_l_mm": 1000,
  "us_r_mm": 900,
  "tof_angle_deg": 90,
  "tof_distance_mm": 850
}
```

### Backend → Brain ESP32 (Commands)
The backend transmits discrete ASCII commands directly to the TCP socket. The Brain ESP32 transparently relays these to the Rover ESP32 via UART.

**Accepted Commands**:
- `FORWARD\n`
- `BACKWARD\n`
- `LEFT\n`
- `RIGHT\n`
- `STOP\n`

## Major Changes from ROS 2
1. **No Middleware**: `rclpy`, `rosbridge_server`, and ROS message schemas have been entirely stripped out.
2. **Direct Socket Handling**: The backend manages its own asynchronous TCP connection to the ESP32.
3. **Internalized Logic**: Legacy ROS nodes (like frontier exploration or occupancy grid mapping) have been ported directly into normal Python classes inside the backend.
4. **Safety E-Stop**: The backend guarantees that any emergency stop or disconnection event immediately transmits a `STOP\n` ASCII command down to the physical hardware.
