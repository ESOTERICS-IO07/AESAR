import math
from typing import List, Tuple

from backend.models.schemas import MapData, Point2D

GRID_RESOLUTION_M = 0.05
GRID_WIDTH = 400
GRID_HEIGHT = 400
GRID_ORIGIN_X = -10.0
GRID_ORIGIN_Y = -10.0

def _bresenham(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
    """Bresenham's Line Algorithm."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = -1 if x0 > x1 else 1
    sy = -1 if y0 > y1 else 1
    
    if dx > dy:
        err = dx / 2.0
        while x != x1:
            points.append((x, y))
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y1:
            points.append((x, y))
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    points.append((x, y))
    return points

class GlobalMapper:
    """
    Maintains a persistent global 2D occupancy grid.
    Updates are transformed using the rover's estimated global pose (x, y, theta).
    """
    def __init__(self) -> None:
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.resolution = GRID_RESOLUTION_M
        self.origin_x = GRID_ORIGIN_X
        self.origin_y = GRID_ORIGIN_Y
        # Initialize grid with -1 (unknown)
        self._grid = bytearray([255] * (self.width * self.height)) 
        
    def get_map_data(self) -> MapData:
        # Convert bytearray to list of ints. Map 255 to -1 for unknown.
        grid_data = [val if val != 255 else -1 for val in self._grid]
        return MapData(
            resolution_m_per_cell=self.resolution,
            width=self.width,
            height=self.height,
            origin=Point2D(x=self.origin_x, y=self.origin_y),
            data=grid_data
        )
        
    def _world_to_grid(self, wx: float, wy: float) -> Tuple[int, int]:
        gx = int(math.floor((wx - self.origin_x) / self.resolution))
        gy = int(math.floor((wy - self.origin_y) / self.resolution))
        return gx, gy
        
    def _grid_to_world(self, gx: int, gy: int) -> Tuple[float, float]:
        wx = (gx * self.resolution) + self.origin_x + (self.resolution / 2.0)
        wy = (gy * self.resolution) + self.origin_y + (self.resolution / 2.0)
        return wx, wy
        
    def update_from_tof(self, pose: Tuple[float, float, float], angle_deg: float, distance_mm: float) -> None:
        """
        Raycasts a single ToF measurement into the global grid.
        pose: (x, y, theta)
        angle_deg: servo angle (90 is straight ahead, 30 is right, 150 is left)
        distance_mm: measured distance. If valid, distance_mm is in [10, 2000].
        """
        rx, ry, rtheta = pose
        
        valid = (10.0 <= distance_mm <= 2000.0) and (abs(distance_mm - 999.0) > 1.0)
        
        # We only raycast up to a max reliable distance for free space if invalid
        dist_m = distance_mm / 1000.0 if valid else 2.0
        
        # 90 deg is straight ahead (+x in rover frame). 30 deg is right (-y in rover frame).
        # Convert servo angle to angle relative to rover's heading
        rel_angle_rad = math.radians(angle_deg - 90.0)
        global_angle = rtheta + rel_angle_rad
        
        # Endpoint in global coordinates
        end_x = rx + dist_m * math.cos(global_angle)
        end_y = ry + dist_m * math.sin(global_angle)
        
        gx0, gy0 = self._world_to_grid(rx, ry)
        gx1, gy1 = self._world_to_grid(end_x, end_y)
        
        ray = _bresenham(gx0, gy0, gx1, gy1)
        if not ray:
            return
            
        # Mark intermediate cells free (0)
        # We don't overwrite verified obstacles (100) with free space lightly, 
        # but for true dynamic mapping, we can overwrite. Let's stick to 0.
        for cx, cy in ray[:-1]:
            if 0 <= cx < self.width and 0 <= cy < self.height:
                idx = cy * self.width + cx
                if self._grid[idx] != 100:
                    self._grid[idx] = 0
                    
        # Mark endpoint cell occupied (100) ONLY if it was a valid reading
        if valid:
            lx, ly = ray[-1]
            if 0 <= lx < self.width and 0 <= ly < self.height:
                self._grid[ly * self.width + lx] = 100
