# ARACHNID Serial Hardware UART Protocols

## 1. Physical Specifications
* **Baud Rate**: `115200`
* **Data Bits**: 8
* **Parity**: None
* **Stop Bits**: 1
* **Framing**: JSON line-delimited (`\n`)

---

## 2. Sensor ESP32 (COM6 / `/dev/ttyUSB0`)

### Stream 1: Range Telemetry (20 Hz)
```json
{"timestamp_ms":1725200000000,"seq":100,"us_fl_mm":450.0,"us_fr_mm":460.0,"us_l_mm":1200.0,"us_r_mm":1180.0,"tof_front_mm":440.0,"sensor_status":{"us_fl":"OK","us_fr":"OK","us_l":"OK","us_r":"OK","tof_front":"OK"}}
```

### Stream 2: IMU Telemetry (20 Hz)
```json
{"timestamp_ms":1725200000000,"seq":100,"accel_x_mps2":0.01,"accel_y_mps2":-0.02,"accel_z_mps2":9.806,"gyro_x_rads":0.001,"gyro_y_rads":-0.001,"gyro_z_rads":0.005}
```

---

## 3. Drive ESP32 (COM5 / `/dev/ttyUSB1`)

### Host → Drive ESP32: Velocity Command (20 Hz)
```json
{"command_id":"CMD-000042","timestamp_ms":1725200000000,"linear_mps":0.25,"angular_rads":0.15,"left_mps":0.229,"right_mps":0.271,"source":"AUTONOMY","e_stop":false}
```

### Drive ESP32 → Host: Wheel Encoder Feedback (20 Hz)
```json
{"timestamp_ms":1725200000000,"left_ticks":1420,"right_ticks":1465,"left_mps":0.229,"right_mps":0.271,"e_stop":false,"watchdog":false}
```
