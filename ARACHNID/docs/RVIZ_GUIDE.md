# ARACHNID RViz Visualization Guide

## 1. Launching RViz
To visualize the real-time state of the rover, occupancy map, planned paths, and frontiers:

```bash
rviz2 -d config/rviz/arachnid.rviz
```

---

## 2. Configured Visual Displays

| Display Item | Topic | Description | Color / Style |
|---|---|---|---|
| **Occupancy Map** | `/map` | 2D Occupancy Grid ($200 \times 200$, $0.05\text{m}$) | Grayscale (Free: Light Gray, Occupied: Black, Unknown: Dark Gray) |
| **Robot Pose** | `/robot_pose` | Current estimated rover position in `map` frame | Green Arrow |
| **Planned Path** | `/planned_path` | Active A* trajectory towards current frontier | Magenta Line |
| **Frontiers** | `/frontiers` | Discovered candidate exploration targets | Yellow / Red Points |
| **TF Tree** | `map` $\to$ `base_link` | Coordinate transformation tree | Coordinate Axes |
