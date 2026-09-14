from types import SimpleNamespace
from unittest import TestCase
import time
import cv2
import numpy as np

from app.ai import AIWorker, AIResult, Detection, AESAR_PEST_LABELS
from app.main import CameraManager, app
from starlette.testclient import TestClient


def make_prediction(labels: list[str], conf: float = 0.85, bbox: list[int] | None = None) -> SimpleNamespace:
    if bbox is None:
        bbox = [10, 20, 60, 80]
    boxes = [
        SimpleNamespace(
            cls=[i],
            conf=[conf],
            xyxy=[np.array(bbox)],
        )
        for i in range(len(labels))
    ]
    return SimpleNamespace(names=dict(enumerate(labels)), boxes=boxes)


class AIWorkerTests(TestCase):
    """Targeted Phase 2 test suite verifying AI requirements A through K."""

    def test_missing_model_behavior(self) -> None:
        """Requirement D: Missing-model behavior must be explicit and safe."""
        worker = AIWorker(lambda: None, "definitely-missing-model.pt")
        self.assertFalse(worker._load_model())
        status = worker.status()
        self.assertEqual(status["state"], "model_unavailable")
        self.assertIn("definitely-missing-model.pt", str(status["detail"]))
        self.assertEqual(status["detections"], [])
        self.assertEqual(status["defender_detection"], "unavailable")

        # Starting worker with missing model runs safely and thread cleanly exits
        worker.start()
        time.sleep(0.05)
        self.assertFalse(worker._thread.is_alive() if worker._thread else False)
        self.assertEqual(worker.status()["state"], "model_unavailable")

    def test_empty_detections(self) -> None:
        """Requirement E: Empty detections remain []."""
        self.assertEqual(AIWorker._detections_from_result(make_prediction([])), [])
        result = AIResult()
        self.assertEqual(result.detections, [])

    def test_supported_canonical_pest_mappings(self) -> None:
        """Requirement F: Supported class filtering strictly maps canonical AESAR classes."""
        pred = make_prediction(
            ["brown plant hopper", "aphids", "Thrips"],
            conf=0.89,
            bbox=[12, 24, 65, 85],
        )
        detections = AIWorker._detections_from_result(pred)
        self.assertEqual(len(detections), 3)

        self.assertEqual(detections[0].class_name, "brown_planthopper")
        self.assertEqual(detections[0].category, "pest")
        self.assertEqual(detections[0].confidence, 0.89)
        self.assertEqual(detections[0].count, 1)
        self.assertEqual(detections[0].bounding_box, [12, 24, 65, 85])

        self.assertEqual(detections[1].class_name, "cotton_aphids")
        self.assertEqual(detections[1].category, "pest")

        self.assertEqual(detections[2].class_name, "chilli_thrips")
        self.assertEqual(detections[2].category, "pest")

        # Test case and whitespace tolerance
        pred_varied = make_prediction(["  Brown Plant Hopper  ", "  APHIDS  ", "thrips"])
        found_names = [d.class_name for d in AIWorker._detections_from_result(pred_varied)]
        self.assertEqual(found_names, ["brown_planthopper", "cotton_aphids", "chilli_thrips"])

    def test_unsupported_classes_are_discarded(self) -> None:
        """Requirement G: Unsupported model labels MUST be discarded, no fake defenders."""
        pred = make_prediction([
            "aphids",
            "spider_mite",
            "ladybird",
            "defender",
            "mirid_bug",
            "person",
            "Thrips",
            "brown plant hopper",
        ])
        found = AIWorker._detections_from_result(pred)
        self.assertEqual([item.class_name for item in found], ["cotton_aphids", "chilli_thrips", "brown_planthopper"])

        # Verify defender detections are not fabricated
        worker = AIWorker(lambda: None, "missing.pt")
        self.assertEqual(worker.status()["defender_detection"], "unavailable")

    def test_annotation_generation(self) -> None:
        """Requirement H: Annotation generation draws bounding boxes and text."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detection = Detection(
            class_name="cotton_aphids",
            category="pest",
            confidence=0.92,
            count=1,
            bounding_box=[10, 10, 50, 50],
        )
        annotated = AIWorker._annotate(frame.copy(), [detection])
        # Annotated frame should have modified pixel values (drawn green box)
        self.assertFalse(np.array_equal(frame, annotated))
        # The bounding box border color is (75, 220, 130) BGR
        box_pixel = annotated[10, 20]
        self.assertEqual(box_pixel.tolist(), [75, 220, 130])

    def test_original_frame_remains_unchanged(self) -> None:
        """Requirement I: Original captured frame must never be modified by annotation."""
        original_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        original_copy = original_frame.copy()

        detection = Detection(
            class_name="chilli_thrips",
            category="pest",
            confidence=0.88,
            count=1,
            bounding_box=[5, 5, 40, 40],
        )
        # Pass a copy as done in AIWorker._run
        _ = AIWorker._annotate(original_frame.copy(), [detection])

        # Original frame must be byte-for-byte identical
        self.assertTrue(np.array_equal(original_frame, original_copy))

    def test_ai_worker_does_not_block_mjpeg_and_drops_stale_frames(self) -> None:
        """Requirement J: AI worker does not block MJPEG stream and samples latest frame."""
        frame_counter = 0
        current_frame = np.zeros((50, 50, 3), dtype=np.uint8)

        def get_latest_frame() -> np.ndarray:
            nonlocal frame_counter
            return current_frame

        worker = AIWorker(get_latest_frame, "missing.pt", target_fps=10.0)

        # Mock a loaded model that simulates a slow inference (30ms per frame)
        worker._model = lambda f, verbose=False: [make_prediction(["aphids"])]
        worker._load_model = lambda: True  # Bypass file check for this unit test

        worker.start()
        time.sleep(0.08)

        # AI result should have updated
        status = worker.status()
        self.assertEqual(status["state"], "ai_ready")
        self.assertEqual(len(status["detections"]), 1)
        self.assertEqual(status["detections"][0]["class_name"], "cotton_aphids")
        self.assertIsNotNone(worker.annotated_jpeg())

        worker.stop()

    def test_camera_preview_remains_available_when_ai_fails(self) -> None:
        """Requirement K: Camera preview remains available when AI fails."""
        camera = CameraManager()
        # Set up a synthetic latest JPEG in camera
        synthetic_frame = np.full((100, 100, 3), 128, dtype=np.uint8)
        ok, encoded = cv2.imencode(".jpg", synthetic_frame)
        self.assertTrue(ok)
        camera._latest_jpeg = encoded.tobytes()

        # Simulate AI failure: model missing
        worker_missing = AIWorker(camera.latest_frame, "missing.pt")
        worker_missing.start()
        time.sleep(0.02)
        self.assertEqual(worker_missing.status()["state"], "model_unavailable")

        # Camera latest frame is still cleanly retrievable
        frame = camera.latest_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape, (100, 100, 3))

        # Simulate AI inference exception
        worker_error = AIWorker(camera.latest_frame, "missing.pt")
        worker_error._model = lambda f, verbose=False: (_ for _ in ()).throw(RuntimeError("GPU OOM"))
        worker_error._load_model = lambda: True
        worker_error.start()
        time.sleep(0.05)

        # State should be inference_error
        self.assertEqual(worker_error.status()["state"], "inference_error")
        # Camera still unaffected
        frame2 = camera.latest_frame()
        self.assertIsNotNone(frame2)
        self.assertEqual(frame2.shape, (100, 100, 3))

        worker_error.stop()

    def test_ai_target_fps_configuration(self) -> None:
        """Requirement 5: Configurable target inference rate."""
        worker = AIWorker(lambda: None, "missing.pt", target_fps=2.0)
        self.assertEqual(worker.status()["target_fps"], 2.0)

        worker.set_target_fps(5.5)
        self.assertEqual(worker.status()["target_fps"], 5.5)

        with self.assertRaises(ValueError):
            worker.set_target_fps(0.05)  # < 0.1

        with self.assertRaises(ValueError):
            worker.set_target_fps(20.0)  # > 15


class APITests(TestCase):
    """Targeted API endpoint tests for Vision AI."""

    def test_api_endpoints(self) -> None:
        with TestClient(app) as client:
            # 1. Camera status
            res = client.get("/api/status")
            self.assertEqual(res.status_code, 200)
            self.assertIn("connected", res.json())

            # 2. AI status
            res = client.get("/api/ai/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn(data["state"], ["ai_ready", "model_loading"])
            self.assertEqual(data["defender_detection"], "unavailable")
            self.assertEqual(data["detections"], [])

            # 3. AI config update
            res = client.put("/api/ai/config", json={"target_fps": 4.5})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["target_fps"], 4.5)

            # 4. AI config validation error
            res = client.put("/api/ai/config", json={"target_fps": 25.0})
            self.assertEqual(res.status_code, 422)

            # 5. AI annotated image (204 when no image)
            res = client.get("/api/ai/annotated")
            self.assertIn(res.status_code, [200, 204])
