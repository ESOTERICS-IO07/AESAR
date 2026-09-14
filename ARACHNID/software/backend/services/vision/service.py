from __future__ import annotations

import logging
from typing import Optional

from backend.config.settings import settings
from backend.models.schemas import CanopyView, VisionResult, VisionStatus
from backend.services.vision.base import BaseVisionProvider
from backend.services.vision.mock_provider import MockVisionProvider
from backend.services.vision.preprocessor import ImagePreprocessor, InvalidImageError
from backend.services.vision.remote_provider import RemoteVisionProvider
from backend.services.vision.yolo_provider import YOLOVisionProvider

logger = logging.getLogger("aesar.vision.service")


class VisionService:
    """
    High-level agricultural vision analysis service for AESAR (Person 2).
    Coordinates between YOLOVisionProvider (LIVE mode), RemoteVisionProvider (LIVE distributed),
    and MockVisionProvider (DEMO mode).
    
    Adheres strictly to the AESAR Master Implementation Contract v2.1:
    - Never fabricates detections
    - Clearly reports MODEL_NOT_CONFIGURED if YOLO weights are missing
    - Dispatches cleanly to MockVisionProvider in DEMO mode
    - Validates image integrity via ImagePreprocessor
    """

    def __init__(
        self,
        provider: Optional[BaseVisionProvider] = None,
        model_path: Optional[str] = None,
    ) -> None:
        self.mock_provider = MockVisionProvider()
        self.yolo_provider = YOLOVisionProvider(model_path=model_path)
        self.remote_provider = RemoteVisionProvider(base_url=settings.aesar_vision_url)

        if provider is not None:
            self._active_provider = provider
        elif settings.aesar_mode.upper() == "LIVE":
            if getattr(settings, "vision_provider", "").lower() == "remote":
                self._active_provider = self.remote_provider
                logger.info("VisionService initialized in LIVE mode with RemoteVisionProvider")
            else:
                self._active_provider = self.yolo_provider
                logger.info("VisionService initialized in LIVE mode with YOLOVisionProvider")
        else:
            self._active_provider = self.mock_provider
            logger.info("VisionService initialized in DEMO mode with MockVisionProvider")

    def set_mode(self, mode: str) -> None:
        """Switch active provider based on runtime mode changes."""
        target = mode.upper()
        if target == "LIVE":
            if getattr(settings, "vision_provider", "").lower() == "remote":
                self._active_provider = self.remote_provider
                logger.info("VisionService switched to RemoteVisionProvider (LIVE)")
            else:
                self._active_provider = self.yolo_provider
                logger.info("VisionService switched to YOLOVisionProvider (LIVE)")
        else:
            self._active_provider = self.mock_provider
            logger.info("VisionService switched to MockVisionProvider (DEMO)")

    def get_active_provider(self) -> BaseVisionProvider:
        return self._active_provider

    def is_model_configured(self) -> bool:
        if isinstance(self._active_provider, RemoteVisionProvider):
            return bool(self._active_provider.base_url)
        return self.yolo_provider.is_configured()

    async def analyze_frame(
        self,
        image_bytes: bytes,
        station_id: Optional[int] = None,
        view: Optional[str] = None,
    ) -> VisionResult:
        """
        Analyze an image buffer and return a validated VisionResult.
        Guaranteed not to raise unhandled exceptions or crash.
        """
        norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None

        # 1. Handle missing/empty image buffer
        if not image_bytes:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_UNAVAILABLE,
                error_message="Image buffer is empty or unavailable.",
                provider=self._active_provider.__class__.__name__.lower(),
            )

        # 2. Pre-validate image format
        try:
            _, meta = ImagePreprocessor.preprocess(image_bytes)
        except InvalidImageError as e:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_INVALID,
                error_message=str(e),
                provider=self._active_provider.__class__.__name__.lower(),
            )
        except Exception as e:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_UNAVAILABLE,
                error_message=f"Failed to access image: {e}",
                provider=self._active_provider.__class__.__name__.lower(),
            )

        # 3. Dispatch to active provider
        try:
            result = await self._active_provider.analyze_image(
                image_bytes=image_bytes,
                station_id=station_id,
                view=view,
            )
            # Attach metadata if not present
            if not result.image_metadata and meta:
                result.image_metadata = meta.model_dump()
            return result
        except Exception as e:
            logger.error(f"Vision provider execution failed: {e}")
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=f"Vision provider failure: {e}",
                image_metadata=meta.model_dump(),
                provider=self._active_provider.__class__.__name__.lower(),
            )
