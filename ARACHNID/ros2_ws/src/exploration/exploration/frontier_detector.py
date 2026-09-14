"""ARACHNID Frontier Detector.

Detects frontier cells (free cells adjacent to unknown cells) and groups them
into frontier clusters with centroid locations and sizes.
"""

from collections import deque
from typing import List, Set, Tuple
import numpy as np

from mapping.grid_utils import (
    FREE_VALUE,
    HEIGHT,
    UNKNOWN_VALUE,
    WIDTH,
    is_in_bounds,
)


class FrontierDetector:
    """Detects and clusters exploration frontiers in 2D occupancy grid."""

    @staticmethod
    def is_frontier_cell(grid: np.ndarray, gx: int, gy: int) -> bool:
        """A cell is a frontier cell if it is FREE (0) and at least one 8-neighbor is UNKNOWN (-1)."""
        if grid[gy, gx] != FREE_VALUE:
            return False

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = gx + dx, gy + dy
                if is_in_bounds(nx, ny):
                    if grid[ny, nx] == UNKNOWN_VALUE:
                        return True
        return False

    @staticmethod
    def detect_frontier_cells(grid: np.ndarray) -> List[Tuple[int, int]]:
        """Find all individual frontier cells in the grid."""
        frontier_cells: List[Tuple[int, int]] = []
        height, width = grid.shape

        for gy in range(1, height - 1):
            for gx in range(1, width - 1):
                if FrontierDetector.is_frontier_cell(grid, gx, gy):
                    frontier_cells.append((gx, gy))

        return frontier_cells

    @staticmethod
    def cluster_frontiers(
        frontier_cells: List[Tuple[int, int]],
        min_cluster_size: int = 2,
    ) -> List[Tuple[float, float, int]]:
        """Cluster adjacent frontier cells using BFS connected-component grouping.

        Args:
            frontier_cells: List of (gx, gy) frontier cell coordinates.
            min_cluster_size: Minimum cells required to form a valid frontier cluster.

        Returns:
            List of tuples: (centroid_gx, centroid_gy, cluster_size)
        """
        cell_set: Set[Tuple[int, int]] = set(frontier_cells)
        visited: Set[Tuple[int, int]] = set()
        clusters: List[Tuple[float, float, int]] = []

        for cell in frontier_cells:
            if cell in visited:
                continue

            # BFS cluster traversal
            queue = deque([cell])
            visited.add(cell)
            current_cluster: List[Tuple[int, int]] = []

            while queue:
                curr = queue.popleft()
                current_cluster.append(curr)
                cx, cy = curr

                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        neighbor = (cx + dx, cy + dy)
                        if neighbor in cell_set and neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

            if len(current_cluster) >= min_cluster_size:
                avg_gx = sum(c[0] for c in current_cluster) / float(len(current_cluster))
                avg_gy = sum(c[1] for c in current_cluster) / float(len(current_cluster))
                clusters.append((avg_gx, avg_gy, len(current_cluster)))

        return clusters