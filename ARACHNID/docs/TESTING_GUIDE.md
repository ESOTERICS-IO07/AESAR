# ARACHNID Contract & Verification Testing Guide

## 1. Running the Automated Test Suite

### Linux / macOS
```bash
export PYTHONPATH="$PWD/ros2_ws/src/sensor_interface:$PWD/ros2_ws/src/odometry:$PWD/ros2_ws/src/localization:$PWD/ros2_ws/src/mapping:$PWD/ros2_ws/src/exploration:$PWD/ros2_ws/src/navigation:$PWD/ros2_ws/src/motor_bridge:$PWD/ros2_ws/src/arachnid_bringup"
pytest tests/contract/ -v
```

### Windows (PowerShell)
```powershell
$env:PYTHONPATH="d:\Desktop\arachnid\ros2_ws\src\sensor_interface;d:\Desktop\arachnid\ros2_ws\src\odometry;d:\Desktop\arachnid\ros2_ws\src\localization;d:\Desktop\arachnid\ros2_ws\src\mapping;d:\Desktop\arachnid\ros2_ws\src\exploration;d:\Desktop\arachnid\ros2_ws\src\navigation;d:\Desktop\arachnid\ros2_ws\src\motor_bridge;d:\Desktop\arachnid\ros2_ws\src\arachnid_bringup"
py -m pytest tests/contract/ -v
```

---

## 2. Test Coverage Overview
* `test_contract_topics_and_schemas.py`: Exact field checks, packet types, coordinate frames, enums.
* `test_config_contracts.py`: Validates all YAML config values against Contract v1.0.0.
* `test_launch_files.py`: Validates launch file structure and dependencies.
* `test_modular_motor_bridge.py`: Tests `SerialBridge`, `MotorWatchdog`, and `PacketBuilder`.
* `test_sensor_interface.py`: Digital filters and serial parsing.
* `test_odometry.py`: Differential drive kinematics and IMU fusion.
* `test_localization.py`: Map frame pose estimation and confidence.
* `test_mapping.py`: Raycasting, grid coordinate transformations, and obstacle updates.
* `test_exploration.py`: Frontier clustering, scoring, and target selection.
* `test_navigation.py`: A* path search, obstacle avoidance safety thresholds, pure pursuit velocity generation.
* `test_end_to_end_autonomy.py`: Complete autonomy pipeline execution from sensors to motor outputs.
