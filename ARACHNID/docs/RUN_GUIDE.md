# ARACHNID Execution & Run Guide

## 1. Prerequisites
* ROS 2 Humble / Iron / Rolling
* Python 3.10+
* `pyserial`, `numpy`, `PyYAML`, `pytest`

---

## 2. Launching the Autonomy Stack

### Tier 1: Sensors, Odometry & Localization Only
```bash
ros2 launch arachnid_bringup sensors.launch.py
```

### Tier 2: Sensors + Occupancy Grid Mapping
```bash
ros2 launch arachnid_bringup mapping.launch.py
```

### Tier 3: Navigation + Motor Bridge
```bash
ros2 launch arachnid_bringup navigation.launch.py
```

### Tier 4: Autonomous Frontier Exploration
```bash
ros2 launch arachnid_bringup autonomy.launch.py
```

### Tier 5: Full Autonomous System
```bash
ros2 launch arachnid_bringup full_system.launch.py
```

---

## 3. Running in Mock / Simulation Mode
To run without physical hardware connected:
```bash
ros2 launch arachnid_bringup full_system.launch.py mock_mode:=true
```
All nodes will generate synthetic sensor readings, simulate wheel kinematics, and execute full autonomous mapping and navigation cycles.
