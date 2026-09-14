"""ARACHNID Map Metrics & Visualizer Helper.

Computes exploration coverage, obstacle statistics, and grid status.
"""

from typing import Dict
import numpy as np

from mapping.grid_utils import FREE_VALUE, OCCUPIED_VALUE, UNKNOWN_VALUE


class MapVisualizer:
    """Provides statistical summaries and analysis of the occupancy grid."""

    @staticmethod
    def explored_percentage(grid: np.ndarray) -> float:
        """Calculate percentage of grid cells explored (non-unknown)."""
        if grid is None or grid.size == 0:
            return 0.0
        known = int(np.sum(grid != UNKNOWN_VALUE))
        total = grid.size
        return round((known / float(total)) * 100.0, 2)

    @staticmethod
    def obstacle_count(grid: np.ndarray) -> int:
        """Return total count of cells marked occupied."""
        if grid is None or grid.size == 0:
            return 0
        return int(np.sum(grid == OCCUPIED_VALUE))

    @staticmethod
    def free_cell_count(grid: np.ndarray) -> int:
        """Return total count of cells marked free."""
        if grid is None or grid.size == 0:
            return 0
        return int(np.sum(grid == FREE_VALUE))

    @staticmethod
    def map_summary(grid: np.ndarray) -> Dict[str, float]:
        """Return comprehensive map exploration summary."""
        return {
            "explored_pct": MapVisualizer.explored_percentage(grid),
            "obstacle_cells": MapVisualizer.obstacle_count(grid),
            "free_cells": MapVisualizer.free_cell_count(grid),
            "total_cells": int(grid.size) if grid is not None else 0,
        }