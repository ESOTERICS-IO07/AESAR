"""Unit & Contract Tests for mapping package."""

import pytest
from mapping.grid_utils import (
    FREE_VALUE,
    HEIGHT,
    OCCUPIED_VALUE,
    ORIGIN_X,
    ORIGIN_Y,
    RESOLUTION,
    UNKNOWN_VALUE,
    WIDTH,
    create_grid,
    get_cell_value,
    grid_to_world,
    is_in_bounds,
    set_free,
    set_occupied,
    world_to_grid,
)
from mapping.map_visualizer import MapVisualizer
from mapping.ray_casting import (
    bresenham,
    sensor_endpoint,
    transform_sensor_to_world,
)


def test_grid_creation():
    grid = create_grid()
    assert grid.shape == (HEIGHT, WIDTH)
    assert (grid == UNKNOWN_VALUE).all()


def test_coordinate_conversions():
    # World (0, 0) should be at grid cell (100, 100) since origin is (-5.0, -5.0) and res=0.05
    gx, gy = world_to_grid(0.0, 0.0)
    assert gx == 100
    assert gy == 100

    # Grid (100, 100) center to world
    wx, wy = grid_to_world(100, 100)
    assert wx == pytest.approx(0.025, abs=1e-3)
    assert wy == pytest.approx(0.025, abs=1e-3)


def test_bounds_and_cell_updates():
    grid = create_grid()
    assert is_in_bounds(0, 0)
    assert is_in_bounds(199, 199)
    assert not is_in_bounds(-1, 0)
    assert not is_in_bounds(200, 200)

    set_free(grid, 100, 100)
    assert get_cell_value(grid, 100, 100) == FREE_VALUE

    set_occupied(grid, 101, 101)
    assert get_cell_value(grid, 101, 101) == OCCUPIED_VALUE


def test_bresenham():
    points = bresenham(0, 0, 3, 3)
    assert points[0] == (0, 0)
    assert points[-1] == (3, 3)
    assert len(points) == 4


def test_transform_sensor_to_world():
    # Robot at (0, 0) with yaw = 0
    # Sensor mount at (0.15, 0.08) with mount_yaw = +0.349
    sx, sy, syaw = transform_sensor_to_world(
        robot_x=0.0,
        robot_y=0.0,
        robot_yaw=0.0,
        mount_x=0.15,
        mount_y=0.08,
        mount_yaw=0.349,
    )
    assert sx == pytest.approx(0.15, abs=1e-3)
    assert sy == pytest.approx(0.08, abs=1e-3)
    assert syaw == pytest.approx(0.349, abs=1e-3)


def test_map_visualizer():
    grid = create_grid()
    assert MapVisualizer.explored_percentage(grid) == 0.0
    assert MapVisualizer.obstacle_count(grid) == 0

    set_free(grid, 50, 50)
    set_occupied(grid, 50, 51)
    assert MapVisualizer.explored_percentage(grid) > 0.0
    assert MapVisualizer.obstacle_count(grid) == 1
