# ARACHNID Sensor ESP32 Firmware

## Overview
This firmware runs on the primary sensor acquisition ESP32 microcontroller, reading 4 ultrasonic distance sensors, 1 Time-of-Flight (VL53L0X) sensor, and a 6-axis IMU (MPU6050). It formats the sensor telemetry into JSON packets strictly matching the **ARACHNID Software Integration Contract v1.0.0** (`RangePacket` and `ImuPacket`) and streams them over UART at 115200 baud at 20 Hz.

## Pinout Configuration

| Component | ESP32 Pin | Description |
|-----------|-----------|-------------|
| **HC-SR04 FL** | GPIO 5 (Trig), GPIO 18 (Echo) | Front-Left Ultrasonic |
| **HC-SR04 FR** | GPIO 19 (Trig), GPIO 21 (Echo) | Front-Right Ultrasonic |
| **HC-SR04 L**  | GPIO 22 (Trig), GPIO 23 (Echo) | Left Ultrasonic |
| **HC-SR04 R**  | GPIO 25 (Trig), GPIO 26 (Echo) | Right Ultrasonic |
| **VL53L0X ToF** | GPIO 16 (SDA), GPIO 17 (SCL) | Front Time-of-Flight (I2C) |
| **MPU6050 IMU** | GPIO 16 (SDA), GPIO 17 (SCL) | 6-DOF IMU (I2C) |

## Required Arduino Libraries
* `ArduinoJson` (v6.x or v7.x)
* `Adafruit VL53L0X`
* `Adafruit MPU6050`
* `Adafruit Sensor`

## Flashing Instructions
1. Open `sensor_esp32.ino` in Arduino IDE or PlatformIO.
2. Select Board: `ESP32 Dev Module`.
3. Select Port (e.g., `COM6` on Windows, `/dev/ttyUSB0` on Linux).
4. Set Upload Speed: `921600` and Flash Frequency: `80MHz`.
5. Upload firmware to ESP32.
