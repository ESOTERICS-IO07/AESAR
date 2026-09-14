from __future__ import annotations

import asyncio
import io
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
from PIL import Image, ImageDraw

try:
    import cv2  # type: ignore
except ImportError:
    cv2 = None

from backend.config.settings import settings
from backend.models.schemas import CameraConfigRequest, CameraState, CameraStatus

logger = logging.getLogger("aesar.camera")


class BaseCameraProvider(ABC):
    """Abstract interface for camera frames."""

    @abstractmethod
    async def capture_frame(self) -> bytes:
        """Capture and return JPEG image bytes."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Check if camera source is reachable."""
        pass

    def release(self) -> None:
        """Optional cleanup/release hook for hardware devices."""
        pass


class LocalWebcamProvider(BaseCameraProvider):
    """
    Connects to the laptop's built-in webcam or USB video camera using OpenCV.
    Operates synchronously on a worker thread via asyncio.to_thread to keep the
    FastAPI event loop completely unblocked and avoid any FPS lag.
    Caches the opened device to avoid expensive re-initialization on every frame.
    """

    def __init__(self, camera_index: int = 0, timeout_seconds: float = 3.0) -> None:
        self.camera_index = camera_index
        self.timeout_seconds = timeout_seconds
        self._cap: Any = None
        self._lock = asyncio.Lock()

    def _get_api_backend(self) -> int:
        if cv2 is None:
            return 0
        return getattr(cv2, "CAP_DSHOW", 700) if os.name == "nt" else getattr(cv2, "CAP_ANY", 0)

    def _ensure_capture_open(self) -> Any:
        if cv2 is None:
            raise RuntimeError("OpenCV (cv2) is not installed in the environment.")
        if self._cap is not None and self._cap.isOpened():
            return self._cap

        backend = self._get_api_backend()
        logger.info(f"Opening local webcam index {self.camera_index} (backend: {backend})...")
        cap = cv2.VideoCapture(self.camera_index, backend)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            raise ConnectionError(f"Cannot open local camera index {self.camera_index}")

        try:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        except Exception:
            pass

        self._cap = cap
        return self._cap

    def _capture_frame_sync(self) -> bytes:
        cap = self._ensure_capture_open()
        ret, frame = cap.read()
        if not ret or frame is None:
            logger.warning("Local webcam read returned empty frame, retrying once...")
            self._release_sync()
            cap = self._ensure_capture_open()
            ret, frame = cap.read()

        if not ret or frame is None:
            raise RuntimeError(f"Failed to read valid frame from local webcam index {self.camera_index}")

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        success, buffer = cv2.imencode(".jpg", frame, encode_param)
        if not success or buffer is None:
            raise RuntimeError("Failed to encode webcam frame to JPEG format")
        return bytes(buffer)

    async def capture_frame(self) -> bytes:
        """Capture and return JPEG image bytes asynchronously without blocking event loop."""
        async with self._lock:
            return await asyncio.to_thread(self._capture_frame_sync)

    def _check_health_sync(self) -> bool:
        try:
            cap = self._ensure_capture_open()
            return bool(cap.isOpened())
        except Exception as e:
            logger.debug(f"Local webcam health check failed: {e}")
            return False

    async def check_health(self) -> bool:
        """Check if local camera can be opened."""
        return await asyncio.to_thread(self._check_health_sync)

    def _release_sync(self) -> None:
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def release(self) -> None:
        """Release camera hardware cleanly."""
        self._release_sync()

    def set_camera_index(self, new_index: int) -> None:
        if self.camera_index != new_index:
            self._release_sync()
            self.camera_index = new_index

    def __del__(self) -> None:
        self._release_sync()


class HttpCameraProvider(BaseCameraProvider):
    """
    Connects to physical IP Webcam running on Android phone.
    Default snapshot URL format: http://<phone_ip>:8080/shot.jpg
    """

    def __init__(self, snapshot_url: str, timeout_seconds: float = 3.0, max_retries: int = 2) -> None:
        self.snapshot_url = snapshot_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    async def capture_frame(self) -> bytes:
        if not self.snapshot_url:
            raise ConnectionError("Camera snapshot URL is not configured")

        last_err: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.get(self.snapshot_url)
                    if resp.status_code == 200 and resp.content:
                        return resp.content
                    raise RuntimeError(f"Camera returned HTTP {resp.status_code}")
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    await asyncio.sleep(0.3 * (attempt + 1))

        raise ConnectionError(f"Failed to capture frame from {self.snapshot_url} after retries: {last_err}")

    async def check_health(self) -> bool:
        if not self.snapshot_url:
            return False
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.head(self.snapshot_url)
                if resp.status_code < 400:
                    return True
                # Some IP Webcams do not support HEAD, try GET with range or short read
                resp = await client.get(self.snapshot_url, headers={"Range": "bytes=0-1024"})
                return resp.status_code in (200, 206)
        except Exception:
            return False


class SimulatedCameraProvider(BaseCameraProvider):
    """
    Generates synthetic agricultural scouting frames for DEMO mode and hardware-free simulation.
    Creates high-definition plant leaf images with station metadata and visual insect markers.
    """

    def __init__(self) -> None:
        self._frame_count = 0

    async def capture_frame(self, station_id: Optional[int] = None) -> bytes:
        self._frame_count += 1
        st_num = station_id if station_id is not None else (self._frame_count % 10) + 1

        # Create synthetic leaf image
        width, height = 640, 480
        # Varied background plant colors based on station
        bg_colors = [
            (34, 110, 45),   # healthy green
            (45, 120, 50),   # deep green
            (85, 125, 40),   # slight yellowing/stress
            (30, 105, 40),   # rich foliage
            (100, 115, 35),  # moderate chlorosis/stress
            (38, 115, 48),   # normal crop
            (90, 100, 30),   # stressed foliage
            (35, 112, 42),   # green canopy
            (42, 118, 46),   # normal leaf
            (33, 108, 44),   # standard crop
        ]
        base_color = bg_colors[(st_num - 1) % len(bg_colors)]
        img = Image.new("RGB", (width, height), color=base_color)
        draw = ImageDraw.Draw(img)

        # Draw leaf veins
        draw.line([(width // 2, 0), (width // 2, height)], fill=(50, 140, 60), width=4)
        for y in range(60, height, 50):
            draw.line([(width // 2, y), (50, y - 40)], fill=(45, 135, 55), width=2)
            draw.line([(width // 2, y), (width - 50, y - 40)], fill=(45, 135, 55), width=2)

        # Station-specific insect dots simulation
        # Station 3, 5, 7, 8 have higher pests (red/yellow dots: aphids/thrips)
        if st_num in (3, 5, 7, 8):
            for i in range(12):
                x = 100 + (i * 37) % 400
                y = 120 + (i * 29) % 250
                draw.ellipse([x, y, x + 6, y + 6], fill=(220, 200, 50), outline=(150, 120, 20))  # Aphids
        # Station 1, 2, 4, 9 have beneficial defenders (orange/black dots: ladybirds)
        if st_num in (1, 2, 4, 9):
            for i in range(4):
                x = 200 + (i * 70) % 300
                y = 150 + (i * 65) % 200
                draw.ellipse([x, y, x + 12, y + 10], fill=(210, 40, 30), outline=(0, 0, 0))  # Ladybird
                draw.ellipse([x + 3, y + 2, x + 5, y + 4], fill=(0, 0, 0))

        # Synthetic HUD banner
        draw.rectangle([(0, 0), (width, 42)], fill=(15, 23, 42))
        draw.text(
            (15, 12),
            f"AESAR SCOUTING FRAME | Station {st_num} | Mode: SIMULATED DEMO | {time.strftime('%Y-%m-%d %H:%M:%S')}",
            fill=(255, 255, 255),
        )

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()

    async def check_health(self) -> bool:
        return True


class CameraService:
    """
    High-level Camera Service for AESAR.
    Supports local laptop webcam (LocalWebcamProvider), HTTP IP Webcam (HttpCameraProvider),
    and fallback simulated provider (SimulatedCameraProvider).
    """

    def __init__(self) -> None:
        self.enabled = settings.camera_enabled
        self.provider_name: str = settings.camera_provider.lower()  # "local", "http", "simulated"
        self.local_camera_index: int = settings.local_camera_index
        self.stream_url = settings.camera_stream_url
        self.snapshot_url = settings.camera_snapshot_url
        self.timeout_seconds = settings.camera_timeout_seconds
        self.analysis_interval_seconds = settings.camera_analysis_interval_seconds

        self._state = CameraState.OFFLINE
        self._last_snapshot: Optional[bytes] = None
        self._last_snapshot_timestamp: Optional[float] = None
        self._last_error: Optional[str] = None

        self.local_provider = LocalWebcamProvider(self.local_camera_index, self.timeout_seconds)
        self.http_provider = HttpCameraProvider(self.snapshot_url, self.timeout_seconds)
        self.simulated_provider = SimulatedCameraProvider()

        # In DEMO mode, start ready with simulated provider
        if settings.aesar_mode.upper() == "DEMO" or self.provider_name == "simulated":
            self._state = CameraState.READY
        elif self.enabled:
            self._state = CameraState.CONNECTING
        else:
            self._state = CameraState.OFFLINE

    def update_config(self, req: CameraConfigRequest) -> CameraStatus:
        """Dynamically update camera URL, provider, or enabled state from API."""
        if req.enabled is not None:
            self.enabled = req.enabled

        if req.provider is not None:
            old_provider = self.provider_name
            self.provider_name = req.provider.lower()
            if old_provider == "local" and self.provider_name != "local":
                self.local_provider.release()

        if req.local_camera_index is not None:
            self.local_camera_index = req.local_camera_index
            self.local_provider.set_camera_index(req.local_camera_index)

        if req.stream_url is not None:
            self.stream_url = req.stream_url

        if req.snapshot_url is not None:
            self.snapshot_url = req.snapshot_url
            self.http_provider.snapshot_url = req.snapshot_url

        if req.analysis_interval_seconds is not None:
            self.analysis_interval_seconds = req.analysis_interval_seconds

        if not self.enabled:
            self._state = CameraState.OFFLINE
        elif settings.aesar_mode.upper() == "DEMO" or self.provider_name == "simulated":
            self._state = CameraState.READY
        else:
            self._state = CameraState.CONNECTING

        return self.get_status()

    def get_status(self) -> CameraStatus:
        """Return the current camera health and status."""
        return CameraStatus(
            state=self._state,
            connected=(self._state in (CameraState.ONLINE, CameraState.READY)),
            provider=self.provider_name,
            camera_index=self.local_camera_index if self.provider_name == "local" else None,
            stream_url=self.stream_url,
            snapshot_url=self.snapshot_url,
            enabled=self.enabled,
            last_snapshot_timestamp=self._last_snapshot_timestamp,
            last_error=self._last_error,
        )

    async def check_health(self) -> bool:
        """Perform active health ping against camera provider."""
        if not self.enabled:
            self._state = CameraState.OFFLINE
            return False

        if settings.aesar_mode.upper() == "DEMO" or self.provider_name == "simulated":
            self._state = CameraState.READY
            self._last_error = None
            return True

        active_provider: BaseCameraProvider = (
            self.local_provider if self.provider_name == "local" else self.http_provider
        )
        reachable = await active_provider.check_health()
        if reachable:
            self._state = CameraState.READY
            self._last_error = None
        else:
            self._state = CameraState.CAMERA_UNAVAILABLE
            self._last_error = (
                f"Cannot open local camera index {self.local_camera_index}"
                if self.provider_name == "local"
                else f"Cannot reach camera at {self.snapshot_url}"
            )
        return reachable

    async def capture_snapshot(self, station_id: Optional[int] = None) -> bytes:
        """
        Capture a JPEG snapshot.
        If in LIVE mode and camera is offline, sets CAMERA_UNAVAILABLE and raises.
        DOES NOT generate a fake frame in LIVE mode.
        In DEMO mode, returns synthetic frame.
        """
        self._state = CameraState.CAPTURING

        # 1. DEMO Mode
        if settings.aesar_mode.upper() == "DEMO" or self.provider_name == "simulated":
            frame = await self.simulated_provider.capture_frame(station_id=station_id)
            self._last_snapshot = frame
            self._last_snapshot_timestamp = time.time()
            self._state = CameraState.READY
            self._last_error = None
            return frame

        # 2. LIVE Mode
        active_provider: BaseCameraProvider = (
            self.local_provider if self.provider_name == "local" else self.http_provider
        )
        try:
            frame = await active_provider.capture_frame()
            self._last_snapshot = frame
            self._last_snapshot_timestamp = time.time()
            self._state = CameraState.READY
            self._last_error = None
            return frame
        except Exception as e:
            self._state = CameraState.CAMERA_UNAVAILABLE
            self._last_error = str(e)
            logger.warning(f"Live camera snapshot failed ({self.provider_name}): {e}")
            # CRITICAL: In LIVE mode, do NOT generate a fake frame!
            raise RuntimeError(f"Camera unavailable ({self.provider_name}): {e}")

    def get_last_snapshot(self) -> Optional[bytes]:
        return self._last_snapshot

    def release(self) -> None:
        """Clean up camera devices on shutdown."""
        self.local_provider.release()
