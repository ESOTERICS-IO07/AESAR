"""Unit & Contract Tests for exploration package."""

import numpy as np
import pytest
from exploration.frontier_detector import FrontierDetector
from exploration.frontier_selector import FrontierSelector
from mapping.grid_utils import create_grid, set_free, set_occupied


def test_frontier_detection():
    grid = create_grid()  # All -1 (Unknown)

    # Clear an area of free cells (0) around center (100, 100)
    for y in range(95, 105):
        for x in range(95, 105):
            grid[y, x] = 0

    # The cells along the border of the cleared area (e.g. x=95, y=95..104) are adjacent to -1
    cells = FrontierDetector.detect_frontier_cells(grid)
    assert len(cells) > 0

    # Cluster these frontier cells
    clusters = FrontierDetector.cluster_frontiers(cells, min_cluster_size=2)
    assert len(clusters) > 0


def test_frontier_selector():
    # Provide two clusters: (centroid_gx, centroid_gy, size)
    clusters = [
        (120.0, 100.0, 10), # Cluster 1: at ~ +1.0m X
        (100.0, 140.0, 5),  # Cluster 2: at ~ +2.0m Y
    ]

    robot_world_pose = (0.0, 0.0)
    frontiers = FrontierSelector.select_frontiers(clusters, robot_world_pose)

    assert len(frontiers) == 2
    assert frontiers[0]["status"] == "SELECTED"
    assert frontiers[1]["status"] == "CANDIDATE"
    assert frontiers[0]["id"] == "F-001"
    assert frontiers[0]["distance_m"] > 0.0
    assert frontiers[0]["score"] >= frontiers[1]["score"]
