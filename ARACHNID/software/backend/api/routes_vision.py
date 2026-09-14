from __future__ import annotations

import base64
import binascii
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel, Field

from backend.models.schemas import CanopyView, VisionResult, VisionStatus
from backend.services.camera_service import CameraService
from backend.services.vision.classes import (
    ALL_CANONICAL_CLASSES,
    CANONICAL_DEFENDERS,
    CANONICAL_DISPLAY_NAMES,
    CANONICAL_PESTS,
    CLASS_TO_CATEGORY,
)
from backend.services.vision.service import VisionService

logger = logging.getLogger("aesar.api.vision")

router = APIRouter(prefix="/vision", tags=["vision"])


class AnalyzeVisionRequest(BaseModel):
    image_base64: Optional[str] = None
    station_id: Optional[int] = None
    view: Optional[str] = Field(default=None, description="Target canopy view: lower, middle, upper")


class VisionStatusResponse(BaseModel):
    active_provider: str
    model_configured: bool
    model_path: Optional[str] = None
    confidence_threshold: float
    canonical_classes_count: int = 11


def create_vision_router(vision_service: VisionService, camera_service: CameraService) -> APIRouter:
    """Creates router for vision AI observation analysis adhering to AESAR Contract v2.1."""

    @router.get("/status", response_model=VisionStatusResponse)
    async def get_vision_status() -> VisionStatusResponse:
        active = vision_service.get_active_provider().__class__.__name__
        is_conf = vision_service.is_model_configured()
        return VisionStatusResponse(
            active_provider=active,
            model_configured=is_conf,
            model_path=getattr(vision_service.yolo_provider, "model_path", None),
            confidence_threshold=vision_service.yolo_provider.confidence_threshold,
        )

    @router.get("/classes")
    async def get_vision_classes() -> Dict[str, Any]:
        return {
            "pests": [
                {"id": p, "display_name": CANONICAL_DISPLAY_NAMES.get(p, p), "category": "pest"}
                for p in CANONICAL_PESTS
            ],
            "defenders": [
                {"id": d, "display_name": CANONICAL_DISPLAY_NAMES.get(d, d), "category": "defender"}
                for d in CANONICAL_DEFENDERS
            ],
            "total_classes": len(ALL_CANONICAL_CLASSES),
        }

    @router.post("/analyze", response_model=VisionResult)
    async def analyze_frame(
        request: Optional[AnalyzeVisionRequest] = None,
    ) -> VisionResult:
        """
        Analyzes an image and returns a contract-validated VisionResult.
        Guaranteed not to crash on malformed inputs, missing camera, or missing model.
        """
        station_id: Optional[int] = None
        view: Optional[str] = None
        image_bytes: Optional[bytes] = None

        if request:
            station_id = request.station_id
            view = request.view
            if request.image_base64:
                try:
                    # Strip data URL prefix if present
                    raw_b64 = request.image_base64
                    if "," in raw_b64:
                        raw_b64 = raw_b64.split(",", 1)[1]
                    image_bytes = base64.b64decode(raw_b64)
                except (binascii.Error, ValueError) as e:
                    logger.warning(f"Vision API received malformed base64 image: {e}")
                    norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None
                    return VisionResult(
                        station_id=station_id,
                        view=norm_view,
                        detections=[],
                        status=VisionStatus.IMAGE_INVALID,
                        error_message=f"Malformed base64 image encoding: {e}",
                    )

        # If no image provided in request body, attempt live camera capture
        if not image_bytes:
            try:
                image_bytes = await camera_service.capture_snapshot(station_id=station_id)
            except Exception as e:
                logger.warning(f"Camera frame capture unavailable: {e}")
                norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None
                return VisionResult(
                    station_id=station_id,
                    view=norm_view,
                    detections=[],
                    status=VisionStatus.IMAGE_UNAVAILABLE,
                    error_message=f"Camera snapshot capture unavailable: {e}",
                )

        if not image_bytes:
            norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_UNAVAILABLE,
                error_message="No image provided and camera is offline.",
            )

        # Run vision service analysis
        result = await vision_service.analyze_frame(
            image_bytes=image_bytes,
            station_id=station_id,
            view=view,
        )
        return result

    @router.post("/analyze-upload", response_model=VisionResult)
    async def analyze_uploaded_file(
        file: UploadFile = File(...),
        station_id: Optional[int] = Form(None),
        view: Optional[str] = Form(None),
    ) -> VisionResult:
        """Multipart form upload endpoint for analyzing raw JPEG/PNG image files."""
        try:
            image_bytes = await file.read()
            return await vision_service.analyze_frame(
                image_bytes=image_bytes,
                station_id=station_id,
                view=view,
            )
        except Exception as e:
            norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_INVALID,
                error_message=f"Failed to read uploaded file: {e}",
            )

    return router
