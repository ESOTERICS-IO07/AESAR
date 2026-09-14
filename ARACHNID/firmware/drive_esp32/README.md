# ARACHNID Drive ESP32 Firmware

## Overview
This firmware runs on the drive motor controller ESP32 microcontroller. It receives JSON velocity and motor speed setpoints from the ROS2 `motor_bridge` node over UART at 115200 baud, executes PWM differential drive control, tracks dual-channel quadrature wheel encoders using hardware interrupts, enforces a 500ms safety watchdog auto-stop, and streams encoder feedback telemetry.

## Pinout Configuration

| Component | ESP32 Pin | Description |
|-----------|-----------|-------------|
| **Left Motor PWM** | GPIO 12 | Motor Driver PWM Speed |
| **Left Motor DIR1** | GPIO 13 | Direction In 1 |
| **Left Motor DIR2** | GPIO 14 | Direction In 2 |
| **Right Motor PWM** | GPIO 27 | Motor Driver PWM Speed |
| **Right Motor DIR1** | GPIO 32 | Direction In 1 |
| **Right Motor DIR2** | GPIO 33 | Direction In 2 |
| **Left Encoder A** | GPIO 34 | Interrupt Channel A |
| **Left Encoder B** | GPIO 35 | Channel B |
| **Right Encoder A** | GPIO 36 | Interrupt Channel A |
| **Right Encoder B** | GPIO 39 | Channel B |

## Required Arduino Libraries
* `ArduinoJson` (v6.x or v7.x)

## Flashing Instructions
1. Open `drive_esp32.ino` in Arduino IDE or PlatformIO.
2. Select Board: `ESP32 Dev Module`.
3. Select Port (e.g., `COM5` on Windows, `/dev/ttyUSB1` on Linux).
4. Set Upload Speed: `921600`.
5. Upload firmware to ESP32.
