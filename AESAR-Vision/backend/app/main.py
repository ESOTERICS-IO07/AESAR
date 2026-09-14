from __future__ import annotations

import threading
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from typing import Iterator, Literal

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, Field

from .ai import AIWorker
from .plant_analysis import PlantVisualWorker


class CameraSourceRequest(BaseModel):
    kind: Literal["local", "ip"]
    device_index: int = Field(default=0, ge=0)
    # Keep this as a string so OpenCV-compatible RTSP as well as HTTP URLs work.
    url: str | None = None

    def capture_target(self) -> int | str:
        if self.kind == "local":
            return self.device_index
        if self.url is None:
            raise ValueError("An IP camera URL is required for an IP source.")
        if not self.url.startswith(("http://", "https://", "rtsp://")):
            raise ValueError("IP camera URL must begin with http://, https://, or rtsp://.")
        return self.url


@dataclass
class CameraStatus:
    source_kind: str = "local"
    source_label: str = "Local camera 0"
    connected: bool = False
    fps: float = 0.0
    clients: int = 0
    error: str | None = None


class CameraManager:
    """Captures in one worker and deliberately stores only the newest JPEG frame."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._source = CameraSourceRequest(kind="local")
        self._capture: cv2.VideoCapture | None = None
        self._worker: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._latest_jpeg: bytes | None = None
        self._frame_ready = threading.Condition(self._lock)
        self._clients = 0
        self._status = CameraStatus()

    def set_source(self, source: CameraSourceRequest) -> dict:
        try:
            target = source.capture_target()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        self.stop()
        with self._lock:
            self._source = source
            self._latest_jpeg = None
            self._status = CameraStatus(
                source_kind=source.kind,
                source_label=f"Local camera {target}" if source.kind == "local" else str(target),
            )
            if self._clients:
                self._start_locked()
        return self.status()

    def status(self) -> dict:
        with self._lock:
            self._status.clients = self._clients
            return asdict(self._status)

    def add_client(self) -> None:
        with self._lock:
            self._clients += 1
            if self._worker is None or not self._worker.is_alive():
                self._start_locked()

    def remove_client(self) -> None:
        should_stop = False
        with self._lock:
            self._clients = max(0, self._clients - 1)
            should_stop = self._clients == 0
        if should_stop:
            self.stop()

    def _start_locked(self) -> None:
        self._stop_event.clear()
        self._worker = threading.Thread(target=self._capture_loop, name="camera-capture", daemon=True)
        self._worker.start()

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            capture = self._capture
        if capture is not None:
            capture.release()  # Unblocks most network/local capture reads.
        worker = self._worker
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=2)
        with self._lock:
            if self._capture is not None:
                self._capture.release()
            self._capture = None
            self._worker = None
            self._status.connected = False
            self._status.fps = 0.0
            self._frame_ready.notify_all()

    def frames(self) -> Iterator[bytes]:
        self.add_client()
        last_frame: bytes | None = None
        try:
            while True:
                with self._frame_ready:
                    self._frame_ready.wait_for(
                        lambda: self._latest_jpeg is not None and self._latest_jpeg != last_frame
                        or self._stop_event.is_set(),
                        timeout=1,
                    )
                    frame = self._latest_jpeg
                if frame is None:
                    continue
                last_frame = frame
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        finally:
            self.remove_client()

    def latest_frame(self) -> np.ndarray | None:
        """Copy just the newest capture for AI without touching the stream path."""
        with self._lock:
            jpeg = self._latest_jpeg
        if jpeg is None:
            return None
        frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
        return frame.copy() if frame is not None else None

    def _capture_loop(self) -> None:
        target = self._source.capture_target()
        capture = cv2.VideoCapture(target)
        # Small buffers favor recency for backends/cameras that support the setting.
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        with self._lock:
            self._capture = capture
            if not capture.isOpened():
                self._status.error = "Could not open camera source."
                self._status.connected = False
                self._frame_ready.notify_all()
                return
            self._status.connected = True
            self._status.error = None

        frame_count = 0
        fps_started = time.monotonic()
        while not self._stop_event.is_set():
            ok, frame = capture.read()
            if not ok:
                with self._lock:
                    self._status.connected = False
                    self._status.error = "Camera frame read failed."
                if self._stop_event.wait(0.1):
                    break
                continue
            ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                continue
            frame_count += 1
            elapsed = time.monotonic() - fps_started
            with self._frame_ready:
                self._latest_jpeg = encoded.tobytes()
                self._status.connected = True
                self._status.error = None
                if elapsed >= 1:
                    self._status.fps = round(frame_count / elapsed, 1)
                    frame_count = 0
                    fps_started = time.monotonic()
                self._frame_ready.notify_all()

        capture.release()


camera = CameraManager()
ai = AIWorker(camera.latest_frame)
plant_worker = PlantVisualWorker(camera.latest_frame)


@asynccontextmanager
async def lifespan(_: FastAPI):
    ai.start()
    plant_worker.start()
    yield
    plant_worker.stop()
    ai.stop()
    camera.stop()


app = FastAPI(title="AESAR-Vision", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/status")
def get_status() -> dict:
    return camera.status()


@app.post("/api/source")
def select_source(source: CameraSourceRequest) -> dict:
    return camera.set_source(source)


@app.get("/api/stream")
def stream() -> StreamingResponse:
    return StreamingResponse(
        camera.frames(), media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
    )


class AIConfigRequest(BaseModel):
    target_fps: float = Field(ge=0.1, le=15)


@app.get("/api/ai/status")
def get_ai_status() -> dict:
    return ai.status()


@app.put("/api/ai/config")
def configure_ai(config: AIConfigRequest) -> dict:
    try:
        return ai.set_target_fps(config.target_fps)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/ai/annotated")
def get_annotated_frame() -> Response:
    image = ai.annotated_jpeg()
    if image is None:
        return Response(status_code=204)
    return Response(content=image, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


class PlantConfigRequest(BaseModel):
    target_fps: float = Field(ge=0.1, le=10.0)


@app.get("/api/plant/status")
def get_plant_status() -> dict:
    return plant_worker.status()


@app.put("/api/plant/config")
def configure_plant(config: PlantConfigRequest) -> dict:
    try:
        return plant_worker.set_target_fps(config.target_fps)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/plant/annotated")
def get_plant_annotated_frame() -> Response:
    image = plant_worker.annotated_jpeg()
    if image is None:
        return Response(status_code=204)
    return Response(content=image, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

