import heapq
import math
from typing import List, Tuple, Optional

from backend.autonomy.mapper import GlobalMapper

class AStarPlanner:
    """
    Implements A* path planning over the global occupancy grid.
    """
    def __init__(self, mapper: GlobalMapper):
        self.mapper = mapper
        
    def _heuristic(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        # Euclidean distance
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
        
    def _is_valid(self, gx: int, gy: int) -> bool:
        if 0 <= gx < self.mapper.width and 0 <= gy < self.mapper.height:
            idx = gy * self.mapper.width + gx
            val = self.mapper._grid[idx]
            # Consider 0 (free space) and 255 (unknown) as traversable for the global planner,
            # but NEVER 100 (obstacle).
            # Wait, if we want strict safety, we might only traverse 0.
            # But exploring unknown space requires planning paths into 255.
            if val != 100:
                return True
        return False
        
    def plan(self, start_pose: Tuple[float, float, float], goal_world: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Plans a path from start_pose to goal_world.
        Returns a list of world coordinates (x, y) forming the path.
        """
        rx, ry, _ = start_pose
        gx0, gy0 = self.mapper._world_to_grid(rx, ry)
        gx1, gy1 = self.mapper._world_to_grid(goal_world[0], goal_world[1])
        
        if not self._is_valid(gx1, gy1):
            return [] # Goal is in an obstacle
            
        open_set = []
        heapq.heappush(open_set, (0.0, gx0, gy0))
        
        came_from = {}
        g_score = {(gx0, gy0): 0.0}
        
        while open_set:
            _, cx, cy = heapq.heappop(open_set)
            
            if cx == gx1 and cy == gy1:
                # Reconstruct path
                path = []
                curr = (cx, cy)
                while curr in came_from:
                    path.append(curr)
                    curr = came_from[curr]
                path.reverse()
                # Convert path to world coords
                world_path = [self.mapper._grid_to_world(x, y) for x, y in path]
                return world_path
                
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = cx + dx, cy + dy
                
                if self._is_valid(nx, ny):
                    cost = math.hypot(dx, dy)
                    tentative_g = g_score[(cx, cy)] + cost
                    
                    if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                        came_from[(nx, ny)] = (cx, cy)
                        g_score[(nx, ny)] = tentative_g
                        f_score = tentative_g + self._heuristic((nx, ny), (gx1, gy1))
                        heapq.heappush(open_set, (f_score, nx, ny))
                        
        return [] # No path found

def get_next_command(pose: Tuple[float, float, float], path: List[Tuple[float, float]]) -> Tuple[str, float, float]:
    """
    Given the current pose and a planned path, determine the next discrete command:
    FORWARD, BACKWARD, LEFT, RIGHT, STOP.
    Returns (command_str, linear_mps, angular_rads).
    """
    if not path:
        return "STOP", 0.0, 0.0
        
    rx, ry, rtheta = pose
    # Find a lookahead point that is at least 0.2m away
    target = path[0]
    for pt in path:
        dist = math.hypot(pt[0] - rx, pt[1] - ry)
        if dist > 0.2:
            target = pt
            break
            
    dx = target[0] - rx
    dy = target[1] - ry
    target_angle = math.atan2(dy, dx)
    
    # Calculate angle difference in [-pi, pi]
    angle_diff = target_angle - rtheta
    angle_diff = math.atan2(math.sin(angle_diff), math.cos(angle_diff))
    
    # Simple control logic mapping to discrete Mode A commands
    # If heading is off by more than ~20 degrees, turn first
    if angle_diff > 0.35:
        return "LEFT", 0.0, 1.0
    elif angle_diff < -0.35:
        return "RIGHT", 0.0, -1.0
    else:
        return "FORWARD", 0.2, 0.0
