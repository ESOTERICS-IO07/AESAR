import math
from typing import List, Tuple, Optional

from backend.autonomy.mapper import GlobalMapper
from backend.models.schemas import Point2D

class FrontierExplorer:
    """
    Implements frontier-based exploration.
    Scans the global occupancy grid to find boundaries between known free space (0)
    and unknown space (255).
    """
    def __init__(self, mapper: GlobalMapper):
        self.mapper = mapper
        
    def find_frontiers(self) -> List[Tuple[float, float]]:
        """
        Finds frontier centroids.
        Returns a list of (x, y) world coordinates.
        """
        width = self.mapper.width
        height = self.mapper.height
        grid = self.mapper._grid
        
        frontiers = []
        visited = bytearray(width * height)
        
        # Simple clustering
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                idx = y * width + x
                
                # If it's free space and not visited
                if grid[idx] == 0 and visited[idx] == 0:
                    # Check if adjacent to unknown space (255)
                    is_frontier_cell = False
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                        n_idx = (y + dy) * width + (x + dx)
                        if grid[n_idx] == 255:
                            is_frontier_cell = True
                            break
                            
                    if is_frontier_cell:
                        # BFS to group frontier cells
                        queue = [(x, y)]
                        visited[idx] = 1
                        cluster = []
                        
                        while queue:
                            cx, cy = queue.pop(0)
                            cluster.append((cx, cy))
                            
                            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                                nx = cx + dx
                                ny = cy + dy
                                if 0 <= nx < width and 0 <= ny < height:
                                    n_idx = ny * width + nx
                                    if visited[n_idx] == 0 and grid[n_idx] == 0:
                                        # Is it a frontier cell?
                                        has_unknown = False
                                        for ddx, ddy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                                            if grid[(ny+ddy)*width + (nx+ddx)] == 255:
                                                has_unknown = True
                                                break
                                        if has_unknown:
                                            visited[n_idx] = 1
                                            queue.append((nx, ny))
                                            
                        if len(cluster) > 3: # Ignore tiny frontiers (noise)
                            # Find centroid
                            sum_x = sum(c[0] for c in cluster)
                            sum_y = sum(c[1] for c in cluster)
                            cent_x = int(sum_x / len(cluster))
                            cent_y = int(sum_y / len(cluster))
                            
                            # Ensure the centroid is actually a free cell from the cluster
                            if grid[cent_y * width + cent_x] != 0:
                                best_c = min(cluster, key=lambda c: (c[0]-cent_x)**2 + (c[1]-cent_y)**2)
                                cent_x, cent_y = best_c[0], best_c[1]
                                
                            frontiers.append(self.mapper._grid_to_world(cent_x, cent_y))
                            
        return frontiers

    def get_best_frontier(self, current_pose: Tuple[float, float, float]) -> Optional[Point2D]:
        """
        Returns the closest frontier centroid.
        """
        frontiers = self.find_frontiers()
        if not frontiers:
            return None
            
        rx, ry, _ = current_pose
        
        # Simple greedy approach: pick the closest frontier
        best_f = min(frontiers, key=lambda f: math.hypot(f[0] - rx, f[1] - ry))
        
        return Point2D(x=best_f[0], y=best_f[1])
