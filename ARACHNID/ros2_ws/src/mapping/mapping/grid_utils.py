"""ARACHNID Occupancy Grid Map Utilities.

Strictly follows ARACHNID Software Integration Contract v1.0.0.
"""

from typing import Optional, Tuple
import numpy as np

# Contract constants
RESOLUTION: float = 0.05
WIDTH: int = 200
HEIGHT: int = 200
ORIGIN_X: float = -5.0
ORIGIN_Y: float = -5.0

UNKNOWN_VALUE: int = -1
FREE_VALUE: int = 0
OCCUPIED_VALUE: int = 100


def create_grid() -> np.ndarray:
    """Initialize a 200x200 grid with UNKNOWN_VALUE (-1)."""
    return np.full((HEIGHT, WIDTH), UNKNOWN_VALUE, dtype=np.int8)


def world_to_grid(x_m: float, y_m: float) -> Tuple[int, int]:
    """Convert world coordinates (metres) to grid indices (col=gx, row=gy)."""
    gx = int(np.floor((x_m - ORIGIN_X) / RESOLUTION))
    gy = int(np.floor((y_m - ORIGIN_Y) / RESOLUTION))
    return gx, gy


def grid_to_world(gx: int, gy: int) -> Tuple[float, float]:
    """Convert grid cell indices (gx, gy) to cell center in world coordinates (metres)."""
    x_m = ORIGIN_X + (gx + 0.5) * RESOLUTION
    y_m = ORIGIN_Y + (gy + 0.5) * RESOLUTION
    return x_m, y_m


def is_in_bounds(gx: int, gy: int) -> bool:
    """Check if grid cell coordinates fall inside grid dimensions."""
    return 0 <= gx < WIDTH and 0 <= gy < HEIGHT


def set_free(grid: np.ndarray, gx: int, gy: int) -> None:
    """Mark a grid cell as FREE (0), preserving occupied cells if desired or overwriting."""
    if is_in_bounds(gx, gy):
        # Do not clear a verified occupied cell unless explicitly clearing
        if grid[gy, gx] != OCCUPIED_VALUE:
            grid[gy, gx] = FREE_VALUE


def set_occupied(grid: np.ndarray, gx: int, gy: int) -> None:
    """Mark a grid cell as OCCUPIED (100)."""
    if is_in_bounds(gx, gy):
        grid[gy, gx] = OCCUPIED_VALUE


def get_cell_value(grid: np.ndarray, gx: int, gy: int) -> Optional[int]:
    """Get cell value at (gx, gy) or None if out of bounds."""
    if is_in_bounds(gx, gy):
        return int(grid[gy, gx])
    return None