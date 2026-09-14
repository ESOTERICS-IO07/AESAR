from unittest import TestCase
import time
import cv2
import numpy as np
from starlette.testclient import TestClient

from app.plant_analysis import (
    PlantVisualResult,
    PlantVisualWorker,
    analyze_plant_frame,
)
from app.main import app


class PlantAnalysisTests(TestCase):
    """Phase 3 tests for lightweight plant visual condition analysis."""

    def test_green_dominant_synthetic_leaf(self) -> None:
        """Requirement 1: Green-dominant synthetic leaf."""
        # 200x200 canvas with gray background (BGR: 100, 100, 100)
        img = np.full((200, 200, 3), 100, dtype=np.uint8)
        # 100x100 green patch (BGR: 34, 139, 34 - ForestGreen)
        img[50:150, 50:150] = [34, 139, 34]

        result, evidence = analyze_plant_frame(img)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.quality, "good")
        self.assertGreaterEqual(result.green_percent, 90.0)
        self.assertLess(result.yellow_percent, 10.0)
        self.assertLess(result.brown_percent, 10.0)
        self.assertGreater(result.leaf_area_percent, 20.0)
        self.assertIsNotNone(evidence)

    def test_yellow_dominant_synthetic_leaf(self) -> None:
        """Requirement 2: Yellow-dominant synthetic leaf."""
        img = np.full((200, 200, 3), 100, dtype=np.uint8)
        # 100x100 vibrant yellow patch (BGR: 0, 215, 255)
        img[50:150, 50:150] = [0, 215, 255]

        result, evidence = analyze_plant_frame(img)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.quality, "good")
        self.assertGreaterEqual(result.yellow_percent, 90.0)
        self.assertLess(result.green_percent, 10.0)
        self.assertLess(result.brown_percent, 10.0)
        self.assertIsNotNone(evidence)

    def test_brown_dry_synthetic_leaf(self) -> None:
        """Requirement 3: Brown/dry synthetic leaf."""
        img = np.full((200, 200, 3), 100, dtype=np.uint8)
        # 100x100 brown patch (BGR: 19, 69, 139 - SaddleBrown)
        img[50:150, 50:150] = [19, 69, 139]

        result, evidence = analyze_plant_frame(img)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.quality, "good")
        self.assertGreaterEqual(result.brown_percent, 85.0)
        self.assertLess(result.green_percent, 15.0)
        self.assertIsNotNone(evidence)

    def test_mixed_color_synthetic_leaf(self) -> None:
        """Requirement 4: Mixed-color synthetic leaf."""
        img = np.full((200, 200, 3), 100, dtype=np.uint8)
        # 50 rows green (50% of leaf area)
        img[50:100, 50:150] = [34, 139, 34]
        # 30 rows yellow (30% of leaf area)
        img[100:130, 50:150] = [0, 215, 255]
        # 20 rows brown (20% of leaf area)
        img[130:150, 50:150] = [19, 69, 139]

        result, evidence = analyze_plant_frame(img)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.quality, "good")
        # Check proportions approximate 50% green, 30% yellow, 20% brown
        self.assertAlmostEqual(result.green_percent, 50.0, delta=8.0)
        self.assertAlmostEqual(result.yellow_percent, 30.0, delta=8.0)
        self.assertAlmostEqual(result.brown_percent, 20.0, delta=8.0)
        # Total percentages should sum to 100.0
        total_pct = result.green_percent + result.yellow_percent + result.brown_percent
        self.assertAlmostEqual(total_pct, 100.0, delta=0.5)

    def test_background_heavy_image(self) -> None:
        """Requirement 5: Background-heavy image (non-plant background)."""
        # Blue desk surface (BGR: 200, 100, 40)
        img = np.full((200, 200, 3), [200, 100, 40], dtype=np.uint8)

        result, evidence = analyze_plant_frame(img)
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.quality, "unavailable")
        self.assertEqual(result.leaf_area_percent, 0.0)

    def test_empty_or_no_usable_plant_region(self) -> None:
        """Requirement 6: Empty/no usable plant region."""
        # Pure black image
        black = np.zeros((100, 100, 3), dtype=np.uint8)
        result, _ = analyze_plant_frame(black)
        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.quality, "unavailable")

        # Neutral gray image
        gray = np.full((100, 100, 3), 128, dtype=np.uint8)
        result_gray, _ = analyze_plant_frame(gray)
        self.assertEqual(result_gray.status, "unavailable")
        self.assertEqual(result_gray.quality, "unavailable")
        self.assertEqual(result_gray.green_percent, 0.0)

    def test_poor_or_invalid_frame(self) -> None:
        """Requirement 7: Poor/invalid frame."""
        # None frame
        res_none, ev_none = analyze_plant_frame(None)
        self.assertEqual(res_none.status, "unavailable")
        self.assertIsNone(ev_none)

        # Zero-sized frame
        res_empty, ev_empty = analyze_plant_frame(np.zeros((0, 0, 3), dtype=np.uint8))
        self.assertEqual(res_empty.status, "unavailable")
        self.assertIsNone(ev_empty)

        # Extreme overexposed frame
        res_white, _ = analyze_plant_frame(np.full((100, 100, 3), 255, dtype=np.uint8))
        self.assertEqual(res_white.status, "unavailable")

    def test_lighting_variation(self) -> None:
        """Requirement 8: Lighting variation where practical."""
        # Normal green leaf patch
        base_img = np.full((200, 200, 3), 100, dtype=np.uint8)
        base_img[50:150, 50:150] = [34, 139, 34]

        # Brightened version
        bright_img = cv2.add(base_img, np.full(base_img.shape, 35, dtype=np.uint8))
        res_bright, _ = analyze_plant_frame(bright_img)
        self.assertEqual(res_bright.status, "ready")
        self.assertGreaterEqual(res_bright.green_percent, 85.0)

        # Dimmed version
        dim_img = cv2.subtract(base_img, np.full(base_img.shape, 30, dtype=np.uint8))
        res_dim, _ = analyze_plant_frame(dim_img)
        self.assertEqual(res_dim.status, "ready")
        self.assertGreaterEqual(res_dim.green_percent, 85.0)

    def test_result_schema_and_immutability(self) -> None:
        """Requirement 9: Result schema & original frame immutability."""
        img = np.full((100, 100, 3), 80, dtype=np.uint8)
        img[20:80, 20:80] = [0, 180, 0]
        original_copy = img.copy()

        result, evidence = analyze_plant_frame(img)

        # Immutability: input frame array was not modified
        self.assertTrue(np.array_equal(img, original_copy))

        # Schema validation
        self.assertIsInstance(result.status, str)
        self.assertIsInstance(result.quality, str)
        self.assertIsInstance(result.green_percent, float)
        self.assertIsInstance(result.yellow_percent, float)
        self.assertIsInstance(result.brown_percent, float)
        self.assertIsInstance(result.leaf_area_percent, float)
        self.assertEqual(result.source, "camera")

    def test_plant_worker_non_blocking_and_latest_frame(self) -> None:
        """Requirement 10 & 11: Worker does not block, drops stale frames."""
        current_frame = np.full((100, 100, 3), 80, dtype=np.uint8)
        current_frame[20:80, 20:80] = [34, 139, 34]

        def get_frame():
            return current_frame

        worker = PlantVisualWorker(get_frame, target_fps=10.0)
        self.assertEqual(worker.status()["target_fps"], 10.0)

        worker.start()
        time.sleep(0.08)

        status = worker.status()
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["quality"], "good")
        self.assertGreaterEqual(status["green_percent"], 85.0)
        self.assertIsNotNone(worker.annotated_jpeg())

        # Config rate update
        worker.set_target_fps(3.0)
        self.assertEqual(worker.status()["target_fps"], 3.0)

        with self.assertRaises(ValueError):
            worker.set_target_fps(0.01)  # < 0.1

        with self.assertRaises(ValueError):
            worker.set_target_fps(25.0)  # > 10.0

        worker.stop()

    def test_plant_fastapi_endpoints(self) -> None:
        """API endpoints verification for plant analysis."""
        with TestClient(app) as client:
            # 1. GET /api/plant/status
            res = client.get("/api/plant/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("green_percent", data)
            self.assertIn("quality", data)
            self.assertIn("leaf_area_percent", data)

            # 2. PUT /api/plant/config
            res_conf = client.put("/api/plant/config", json={"target_fps": 4.0})
            self.assertEqual(res_conf.status_code, 200)
            self.assertEqual(res_conf.json()["target_fps"], 4.0)

            # 3. PUT /api/plant/config validation
            res_invalid = client.put("/api/plant/config", json={"target_fps": 100.0})
            self.assertEqual(res_invalid.status_code, 422)

            # 4. GET /api/plant/annotated
            res_ann = client.get("/api/plant/annotated")
            self.assertIn(res_ann.status_code, [200, 204])
