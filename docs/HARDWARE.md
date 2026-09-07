# Hardware Architecture

This document outlines the known existing ARACHNID hardware architecture and the additions for AESAR.

## Dual ESP32 Architecture
- Brain/Sensor ESP32
- Drive/Motor ESP32

## Drive ESP32 (Existing)
- UART RX GPIO26
- UART TX GPIO25
- 115200 baud
- Drive motor commands:
  - FORWARD
  - BACKWARD
  - LEFT
  - RIGHT
  - STOP
- Drive motor drivers: Dual BTS7960.
- Current motor watchdog: approximately 1000 ms.

## Brain ESP32 (Existing & Additions)
- Wi-Fi SoftAP architecture.

**Existing sensors:**
- 5 ultrasonic sensors
- VL53L0X ToF
- Servo sweep

**AESAR Additions:**
- MPU6050 to be integrated
- Camera to be integrated
- Future soil/environment sensors according to AESAR implementation

**Existing Brain I2C:**
- SDA GPIO21
- SCL GPIO22

The MPU6050 should share the Brain I2C bus with the VL53L0X.

## Critical Restrictions
- Do not modify Drive ESP32 architecture during the initial AESAR implementation.
- Clearly distinguish KNOWN HARDWARE vs AESAR ADDITIONS vs NOT YET VERIFIED HARDWARE.
- Never invent a sensor model or pin assignment.
