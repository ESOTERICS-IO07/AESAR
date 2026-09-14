"""Phase 2 AI worker. It never owns, delays, or queues camera frames."""
from __future__ import annotations
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable
import cv2
import numpy as np

AESAR_PEST_LABELS = {"brown plant hopper": "brown_planthopper", "aphids": "cotton_aphids", "thrips": "chilli_thrips"}

@dataclass
class Detection:
    class_name: str
    category: str
    confidence: float
    count: int
    bounding_box: list[int]

@dataclass
class AIResult:
    state: str = "model_loading"
    detail: str | None = None
    inference_fps: float = 0.0
    target_fps: float = 2.0
    detections: list[Detection] = field(default_factory=list)
    frame_width: int = 0
    frame_height: int = 0
    updated_at: float | None = None
    defender_detection: str = "unavailable"

class AIWorker:
    """Samples a latest-frame getter; slow inference therefore drops stale frames."""
    def __init__(self, latest_frame: Callable[[], np.ndarray | None], model_path: Path | str | None = None, target_fps: float = 2.0) -> None:
        default_path = Path(__file__).resolve().parents[1] / "models" / "aesar-pest-yolo11s.pt"
        self._latest_frame, self._model_path, self._target_fps = latest_frame, Path(model_path or os.getenv("AESAR_VISION_MODEL", str(default_path))), target_fps
        self._lock, self._stop = threading.Lock(), threading.Event()
        self._result, self._annotated_jpeg, self._thread, self._model = AIResult(target_fps=target_fps), None, None, None

    def start(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear(); self._thread = threading.Thread(target=self._run, name="vision-ai", daemon=True); self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None and self._thread is not threading.current_thread(): self._thread.join(timeout=3)
        self._thread, self._model = None, None

    def status(self) -> dict:
        with self._lock: return asdict(self._result)

    def set_target_fps(self, target_fps: float) -> dict:
        if not 0.1 <= target_fps <= 15: raise ValueError("AI target FPS must be between 0.1 and 15.")
        with self._lock: self._target_fps, self._result.target_fps = target_fps, target_fps
        return self.status()

    def annotated_jpeg(self) -> bytes | None:
        with self._lock: return self._annotated_jpeg

    def _set_state(self, state: str, detail: str | None = None) -> None:
        with self._lock: self._result.state, self._result.detail = state, detail

    def _load_model(self) -> bool:
        self._set_state("model_loading")
        if not self._model_path.is_file():
            self._set_state("model_unavailable", f"Checkpoint not found: {self._model_path.name}"); return False
        try:
            # A local validated checkpoint only; never auto-download a generic model.
            from ultralytics import YOLO
            self._model = YOLO(str(self._model_path)); self._set_state("ai_ready"); return True
        except Exception as exc:
            self._set_state("model_unavailable", f"Could not load checkpoint: {exc}"); return False

    def _run(self) -> None:
        if not self._load_model(): return
        while not self._stop.is_set():
            started, frame = time.monotonic(), self._latest_frame()
            if frame is not None:
                try:
                    detections = self._detections_from_result(self._model(frame, verbose=False)[0])
                    ok, jpeg = cv2.imencode(".jpg", self._annotate(frame.copy(), detections), [cv2.IMWRITE_JPEG_QUALITY, 80])
                    elapsed = max(time.monotonic() - started, .001)
                    with self._lock:
                        self._result = AIResult(
                            state="ai_ready",
                            detail=None,
                            inference_fps=round(1 / elapsed, 1),
                            target_fps=self._target_fps,
                            detections=detections,
                            frame_width=int(frame.shape[1]),
                            frame_height=int(frame.shape[0]),
                            updated_at=time.time(),
                            defender_detection="unavailable",
                        )
                        self._annotated_jpeg = jpeg.tobytes() if ok else None
                except Exception as exc: self._set_state("inference_error", str(exc))
            with self._lock: interval = 1 / self._target_fps
            self._stop.wait(max(0, interval - (time.monotonic() - started)))

    @staticmethod
    def _detections_from_result(prediction: Any) -> list[Detection]:
        output: list[Detection] = []
        boxes = getattr(prediction, "boxes", None)
        if boxes is None:
            return output
        names = getattr(prediction, "names", {})
        for box in boxes:
            cls_idx = int(box.cls[0])
            raw_name = names.get(cls_idx) if isinstance(names, dict) else (names[cls_idx] if cls_idx < len(names) else None)
            if raw_name is None and isinstance(names, dict):
                raw_name = names.get(str(cls_idx))
            if raw_name is None:
                continue
            canonical = AESAR_PEST_LABELS.get(str(raw_name).strip().lower())
            if canonical is None:
                continue
            conf = round(float(box.conf[0]), 3)
            xyxy_raw = box.xyxy[0]
            coords = xyxy_raw.tolist() if hasattr(xyxy_raw, "tolist") else list(xyxy_raw)
            bbox = [int(v) for v in coords]
            output.append(Detection(canonical, "pest", conf, 1, bbox))
        return output

    @staticmethod
    def _annotate(frame: np.ndarray, detections: list[Detection]) -> np.ndarray:
        for detection in detections:
            x1, y1, x2, y2 = detection.bounding_box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (75, 220, 130), 2)
            cv2.putText(frame, f"{detection.class_name} {detection.confidence:.0%}", (x1, max(20, y1 - 7)), cv2.FONT_HERSHEY_SIMPLEX, .55, (75, 220, 130), 2)
        return frame
