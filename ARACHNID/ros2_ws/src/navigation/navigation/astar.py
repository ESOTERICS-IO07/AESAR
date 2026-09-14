"""ARACHNID A* Grid Path Planner.

Finds collision-free optimal 8-connected paths on 2D occupancy grids
with obstacle inflation safety margins.
"""

from heapq import heappop, heappush
from typing import Any, Dict, List, Optional, Set, Tuple
import math

import numpy as np

from mapping.grid_utils import (
    HEIGHT,
    OCCUPIED_VALUE,
    UNKNOWN_VALUE,
    WIDTH,
    grid_to_world,
    is_in_bounds,
    world_to_grid,
)


class AStarPlanner:
    """8-connected A* search with obstacle safety inflation."""

    def __init__(self, inflation_radius_cells: int = 3):
        self.inflation_radius = max(0, int(inflation_radius_cells))

    def inflate_obstacles(self, grid: np.ndarray) -> np.ndarray:
        """Create a binary collision mask with inflated obstacle boundaries."""
        height, width = grid.shape
        obstacle_mask = np.zeros((height, width), dtype=bool)

        occupied_coords = np.argwhere(grid == OCCUPIED_VALUE)

        for y, x in occupied_coords:
            for dy in range(-self.inflation_radius, self.inflation_radius + 1):
                for dx in range(-self.inflation_radius, self.inflation_radius + 1):
                    if dx * dx + dy * dy <= self.inflation_radius * self.inflation_radius:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            obstacle_mask[ny, nx] = True

        return obstacle_mask

    def plan_path(
        self,
        grid: np.ndarray,
        start_world: Tuple[float, float],
        goal_world: Tuple[float, float],
    ) -> Optional[List[Dict[str, float]]]:
        """Plan path from start_world (x, y) to goal_world (x, y).

        Returns:
            List of waypoint dicts: [{"x_m": ..., "y_m": ..., "yaw_rad": ...}, ...]
            or None if no valid path exists.
        """
        sx, sy = world_to_grid(start_world[0], start_world[1])
        gx, gy = world_to_grid(goal_world[0], goal_world[1])

        if not is_in_bounds(sx, sy) or not is_in_bounds(gx, gy):
            return None

        # If start and goal are the same cell
        if (sx, sy) == (gx, gy):
            wx, wy = grid_to_world(gx, gy)
            return [{"x_m": round(wx, 2), "y_m": round(wy, 2), "yaw_rad": 0.0}]

        collision_mask = self.inflate_obstacles(grid)

        # Allow start and goal cell even if on margin edge
        collision_mask[sy, sx] = False
        collision_mask[gy, gx] = False

        # Priority queue stores: (f_score, h_score, (x, y))
        open_set: List[Tuple[float, float, Tuple[int, int]]] = []
        heappush(open_set, (self.heuristic(sx, sy, gx, gy), 0.0, (sx, sy)))

        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {(sx, sy): 0.0}
        visited: Set[Tuple[int, int]] = set()

        # 8-connected motion deltas and costs
        motions = [
            (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
            (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142),
        ]

        found = False

        while open_set:
            _, current_g, current = heappop(open_set)

            if current in visited:
                continue
            visited.add(current)

            if current == (gx, gy):
                found = True
                break

            cx, cy = current

            for dx, dy, step_cost in motions:
                nx, ny = cx + dx, cy + dy

                if not is_in_bounds(nx, ny):
                    continue

                if collision_mask[ny, nx] or grid[ny, nx] == OCCUPIED_VALUE:
                    continue

                # Extra minor cost for traversing unknown space vs known free
                cell_cost = 1.2 if grid[ny, nx] == UNKNOWN_VALUE else 1.0
                tentative_g = current_g + step_cost * cell_cost

                neighbor = (nx, ny)
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self.heuristic(nx, ny, gx, gy)
                    heappush(open_set, (tentative_g + h, tentative_g, neighbor))

        if not found:
            return None

        # Reconstruct path
        grid_path: List[Tuple[int, int]] = [(gx, gy)]
        curr = (gx, gy)
        while curr in came_from:
            curr = came_from[curr]
            grid_path.append(curr)
        grid_path.reverse()

        # Convert to world waypoints with smooth headings
        return self._format_waypoints(grid_path)

    @staticmethod
    def heuristic(x1: int, y1: int, x2: int, y2: int) -> float:
        """Euclidean distance heuristic."""
        return math.hypot(x2 - x1, y2 - y1)

    def _format_waypoints(self, grid_path: List[Tuple[int, int]]) -> List[Dict[str, float]]:
        """Subsamples and formats grid path into world waypoints with headings."""
        if not grid_path:
            return []

        # Downsample path every N cells or direction change for smoothness
        sampled: List[Tuple[int, int]] = [grid_path[0]]
        for i in range(1, len(grid_path) - 1):
            prev_cell = grid_path[i - 1]
            curr_cell = grid_path[i]
            next_cell = grid_path[i + 1]

            dir1 = (curr_cell[0] - prev_cell[0], curr_cell[1] - prev_cell[1])
            dir2 = (next_cell[0] - curr_cell[0], next_cell[1] - curr_cell[1])

            if dir1 != dir2 or i % 3 == 0:
                sampled.append(curr_cell)

        sampled.append(grid_path[-1])

        waypoints: List[Dict[str, float]] = []
        for i in range(len(sampled)):
            gx, gy = sampled[i]
            wx, wy = grid_to_world(gx, gy)

            if i < len(sampled) - 1:
                next_wx, next_wy = grid_to_world(sampled[i + 1][0], sampled[i + 1][1])
                yaw = math.atan2(next_wy - wy, next_wx - wx)
            elif len(waypoints) > 0:
                yaw = waypoints[-1]["yaw_rad"]
            else:
                yaw = 0.0

            waypoints.append({
                "x_m": round(wx, 2),
                "y_m": round(wy, 2),
                "yaw_rad": round(yaw, 2),
            })

        return waypoints
