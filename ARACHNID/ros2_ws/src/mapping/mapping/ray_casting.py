"""ARACHNID Sensor Ray Casting & Coordinate Transformations.

Calculates exact sensor mount positions on robot frame and traces ray beams
through the occupancy grid using the Bresenham line algorithm.
"""

from typing import List, Tuple
import math


def bresenham(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Generate grid cell indices from (x0, y0) to (x1, y1) using Bresenham's algorithm."""
    points: List[Tuple[int, int]] = []

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx - dy
    curr_x, curr_y = x0, y0

    while True:
        points.append((curr_x, curr_y))

        if curr_x == x1 and curr_y == y1:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            curr_x += sx

        if e2 < dx:
            err += dx
            curr_y += sy

    return points


def transform_sensor_to_world(
    robot_x: float,
    robot_y: float,
    robot_yaw: float,
    mount_x: float,
    mount_y: float,
    mount_yaw: float,
) -> Tuple[float, float, float]:
    """Calculate world frame position and heading for a mounted sensor.

    Args:
        robot_x, robot_y: Robot base position in world (metres).
        robot_yaw: Robot orientation in world (radians).
        mount_x, mount_y: Sensor position relative to robot body (metres).
        mount_yaw: Sensor angular offset relative to robot body (radians).

    Returns:
        (sensor_world_x, sensor_world_y, sensor_beam_yaw)
    """
    cos_yaw = math.cos(robot_yaw)
    sin_yaw = math.sin(robot_yaw)

    sensor_world_x = robot_x + (mount_x * cos_yaw - mount_y * sin_yaw)
    sensor_world_y = robot_y + (mount_x * sin_yaw + mount_y * cos_yaw)
    sensor_beam_yaw = robot_yaw + mount_yaw

    return sensor_world_x, sensor_world_y, sensor_beam_yaw


def sensor_endpoint(
    sensor_x: float,
    sensor_y: float,
    beam_yaw: float,
    distance_m: float,
) -> Tuple[float, float]:
    """Calculate world coordinates of the sensor ray endpoint."""
    end_x = sensor_x + distance_m * math.cos(beam_yaw)
    end_y = sensor_y + distance_m * math.sin(beam_yaw)
    return end_x, end_y