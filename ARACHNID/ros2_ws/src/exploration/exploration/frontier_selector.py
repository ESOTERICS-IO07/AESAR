"""ARACHNID Frontier Selector.

Converts grid cluster centroids to world coordinates, scores candidates
based on distance and information gain, and selects the primary exploration target.
"""

from typing import Any, Dict, List, Optional, Tuple
import math

from mapping.grid_utils import grid_to_world


class FrontierSelector:
    """Ranks and selects exploration frontiers strictly adhering to Contract v1.0.0."""

    @staticmethod
    def select_frontiers(
        clusters: List[Tuple[float, float, int]],
        robot_world_pose: Tuple[float, float],
        max_frontiers_to_publish: int = 10,
    ) -> List[Dict[str, Any]]:
        """Score and format frontier list adhering to Contract v1.0.0.

        Args:
            clusters: List of (centroid_gx, centroid_gy, cluster_size).
            robot_world_pose: Current robot position (rx_m, ry_m).
            max_frontiers_to_publish: Maximum number of frontiers to include in packet.

        Returns:
            List of Frontier dicts with keys: [id, x_m, y_m, distance_m, score, status]
        """
        if not clusters:
            return []

        rx, ry = robot_world_pose
        scored_candidates: List[Dict[str, Any]] = []

        for gx, gy, size in clusters:
            # Convert centroid grid coords to world coords in metres
            wx, wy = grid_to_world(int(round(gx)), int(round(gy)))
            distance_m = math.hypot(wx - rx, wy - ry)

            # Score function: larger clusters weighted higher, closer frontiers favored
            score = (float(size) * 2.0) / (distance_m + 0.5)

            scored_candidates.append({
                "x_m": round(wx, 2),
                "y_m": round(wy, 2),
                "distance_m": round(distance_m, 2),
                "score": round(score, 2),
                "size": size,
            })

        # Sort descending by score
        scored_candidates.sort(key=lambda item: item["score"], reverse=True)

        results: List[Dict[str, Any]] = []
        for idx, cand in enumerate(scored_candidates[:max_frontiers_to_publish]):
            status = "SELECTED" if idx == 0 else "CANDIDATE"
            results.append({
                "id": f"F-{idx + 1:03d}",
                "x_m": cand["x_m"],
                "y_m": cand["y_m"],
                "distance_m": cand["distance_m"],
                "score": cand["score"],
                "status": status,
            })

        return results