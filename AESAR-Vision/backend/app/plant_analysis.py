"""Phase 3 Plant Visual Condition Analysis.

Provides lightweight classical computer vision analysis for measurable visual
indicators (green, yellow, and brown pixel percentages, leaf area, and analysis
quality). Does NOT perform biological or disease diagnosis.
"""
from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass
from typing import Callable

import cv2
import numpy as np


@dataclass
class PlantVisualResult:
    status: str = "unavailable"  # "ready", "unavailable", "low_quality", "error"
    quality: str = "unavailable"  # "good", "low", "unavailable"
    green_percent: float = 0.0
    yellow_percent: float = 0.0
    brown_percent: float = 0.0
    leaf_area_percent: float = 0.0
    detail: str | None = None
    analysis_fps: float = 0.0
    target_fps: float = 2.0
    updated_at: float | None = None
    source: str = "camera"


def analyze_plant_frame(frame: np.ndarray | None) -> tuple[PlantVisualResult, np.ndarray | None]:
    """Analyzes visual characteristics of plant/leaf tissue in the frame.

    Returns the analysis result and a separate segmentation visualization mask.
    The input frame is never mutated.
    """
    if frame is None or frame.size == 0 or frame.ndim != 3:
        return (
            PlantVisualResult(
                status="unavailable",
                quality="unavailable",
                detail="No valid frame provided for analysis",
            ),
            None,
        )

    h, w = frame.shape[:2]
    total_pixels = h * w
    if total_pixels == 0:
        return (
            PlantVisualResult(
                status="unavailable",
                quality="unavailable",
                detail="Empty frame dimensions",
            ),
            None,
        )

    # Convert to grayscale for basic lighting/quality checks
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))

    # If the image is excessively dark or completely washed out
    if mean_brightness < 6.0 or mean_brightness > 250.0:
        return (
            PlantVisualResult(
                status="unavailable",
                quality="unavailable",
                detail="Extreme lighting condition (overexposed or underexposed frame)",
            ),
            None,
        )

    # Convert BGR to HSV for color segmentation
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Color segmentation bounds (HSV in OpenCV: H: 0-180, S: 0-255, V: 0-255)
    # 1. Green leaf foliage: Hue 33 to 88, Sat >= 35, Val >= 35
    mask_green = cv2.inRange(hsv, np.array([33, 35, 35]), np.array([88, 255, 255])) > 0

    # 2. Yellowing / chlorotic leaf tissue: Hue 20 to 32, Sat >= 40, Val >= 120
    # or Hue 22 to 32, Sat >= 50, Val >= 80
    mask_yellow = (
        (cv2.inRange(hsv, np.array([20, 40, 120]), np.array([32, 255, 255])) > 0)
        | (cv2.inRange(hsv, np.array([22, 50, 80]), np.array([32, 255, 255])) > 0)
    ) & (~mask_green)

    # 3. Brown / dry necrotic leaf tissue: Hue 7 to 22, Sat >= 25, Val between 25 and 160
    mask_brown = (
        (cv2.inRange(hsv, np.array([7, 25, 25]), np.array([22, 230, 160])) > 0)
        & (~mask_green)
        & (~mask_yellow)
    )

    raw_plant = mask_green | mask_yellow | mask_brown

    # Morphological opening to reduce single-pixel speckle noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    clean_plant = cv2.morphologyEx(raw_plant.astype(np.uint8), cv2.MORPH_OPEN, kernel) > 0

    plant_pixel_count = int(np.count_nonzero(clean_plant))
    leaf_area_fraction = plant_pixel_count / total_pixels

    # Threshold: at least 0.8% of the image or 200 pixels must contain plant content
    min_required_pixels = max(200, int(total_pixels * 0.008))
    if plant_pixel_count < min_required_pixels:
        return (
            PlantVisualResult(
                status="unavailable",
                quality="unavailable",
                leaf_area_percent=round(leaf_area_fraction * 100, 1),
                detail="No significant plant or leaf region detected",
            ),
            None,
        )

    # Re-sample specific colors filtered to clean plant mask
    green_count = int(np.count_nonzero(mask_green & clean_plant))
    yellow_count = int(np.count_nonzero(mask_yellow & clean_plant))
    brown_count = int(np.count_nonzero(mask_brown & clean_plant))

    total_classified = green_count + yellow_count + brown_count
    if total_classified == 0:
        return (
            PlantVisualResult(
                status="unavailable",
                quality="unavailable",
                leaf_area_percent=round(leaf_area_fraction * 100, 1),
                detail="Segmented region has insufficient identifiable color",
            ),
            None,
        )

    green_pct = round((green_count / total_classified) * 100.0, 1)
    yellow_pct = round((yellow_count / total_classified) * 100.0, 1)
    # Ensure percentages cleanly sum to 100.0 without floating point drift
    brown_pct = round(max(0.0, 100.0 - (green_pct + yellow_pct)), 1)
    leaf_area_pct = round(leaf_area_fraction * 100.0, 1)

    # Assess analysis quality
    # Low quality if leaf area is very small (< 2.0%) or classified pixels are borderline
    if leaf_area_fraction < 0.02 or total_classified < (min_required_pixels * 1.5):
        quality = "low"
        status = "ready"
        detail = "Low contrast or marginal leaf coverage detected"
    else:
        quality = "good"
        status = "ready"
        detail = None

    result = PlantVisualResult(
        status=status,
        quality=quality,
        green_percent=green_pct,
        yellow_percent=yellow_pct,
        brown_percent=brown_pct,
        leaf_area_percent=leaf_area_pct,
        detail=detail,
        updated_at=time.time(),
        source="camera",
    )

    # Generate separate visual segmentation evidence overlay
    # Background is dimmed, plant regions are colored:
    # Green: (0, 210, 80), Yellow: (0, 220, 255), Brown: (40, 90, 160)
    evidence = (frame.copy() * 0.35).astype(np.uint8)
    evidence[mask_green & clean_plant] = [0, 210, 80]
    evidence[mask_yellow & clean_plant] = [0, 220, 255]
    evidence[mask_brown & clean_plant] = [40, 90, 160]

    return result, evidence


class PlantVisualWorker:
    """Asynchronous worker sampling the newest camera frame for plant condition analysis."""

    def __init__(
        self,
        latest_frame: Callable[[], np.ndarray | None],
        target_fps: float = 2.0,
    ) -> None:
        self._latest_frame = latest_frame
        self._target_fps = target_fps
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._result = PlantVisualResult(target_fps=target_fps)
        self._annotated_jpeg: bytes | None = None

    def start(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="plant-analysis",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=3)
        self._thread = None

    def status(self) -> dict:
        with self._lock:
            return asdict(self._result)

    def set_target_fps(self, target_fps: float) -> dict:
        if not 0.1 <= target_fps <= 10.0:
            raise ValueError("Plant visual analysis target FPS must be between 0.1 and 10.")
        with self._lock:
            self._target_fps = target_fps
            self._result.target_fps = target_fps
        return self.status()

    def annotated_jpeg(self) -> bytes | None:
        with self._lock:
            return self._annotated_jpeg

    def _run(self) -> None:
        while not self._stop.is_set():
            started = time.monotonic()
            frame = self._latest_frame()

            if frame is not None:
                try:
                    result, evidence = analyze_plant_frame(frame)
                    jpeg_bytes = None
                    if evidence is not None:
                        ok, encoded = cv2.imencode(
                            ".jpg",
                            evidence,
                            [cv2.IMWRITE_JPEG_QUALITY, 80],
                        )
                        if ok:
                            jpeg_bytes = encoded.tobytes()

                    elapsed = max(time.monotonic() - started, 0.001)
                    with self._lock:
                        result.analysis_fps = round(1.0 / elapsed, 1)
                        result.target_fps = self._target_fps
                        self._result = result
                        self._annotated_jpeg = jpeg_bytes
                except Exception as exc:
                    with self._lock:
                        self._result = PlantVisualResult(
                            status="error",
                            quality="unavailable",
                            detail=f"Analysis error: {exc}",
                            target_fps=self._target_fps,
                        )

            with self._lock:
                interval = 1.0 / self._target_fps
            self._stop.wait(max(0.0, interval - (time.monotonic() - started)))
