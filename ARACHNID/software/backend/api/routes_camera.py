from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from backend.models.schemas import CameraConfigRequest, CameraStatus
from backend.services.camera_service import CameraService

logger = logging.getLogger("aesar.api.camera")

router = APIRouter(prefix="/camera", tags=["camera"])


def create_camera_router(camera_service: CameraService) -> APIRouter:
    """Creates router for camera status, configuration, and image snapshot streaming."""

    @router.get("/status", response_model=CameraStatus)
    async def get_camera_status() -> CameraStatus:
        return camera_service.get_status()

    @router.post("/config", response_model=CameraStatus)
    async def update_camera_config(config: CameraConfigRequest) -> CameraStatus:
        status = camera_service.update_config(config)
        logger.info(
            f"Camera config updated: provider={status.provider}, camera_index={status.camera_index}, "
            f"enabled={status.enabled}, snapshot_url={status.snapshot_url}"
        )
        return status

    @router.get("/snapshot")
    async def get_camera_snapshot() -> Response:
        try:
            snapshot_bytes = await camera_service.capture_snapshot()
            if not snapshot_bytes:
                raise HTTPException(status_code=503, detail="Camera unable to capture frame")
            return Response(content=snapshot_bytes, media_type="image/jpeg")
        except Exception as e:
            logger.error(f"Failed to capture snapshot: {e}")
            raise HTTPException(status_code=503, detail=f"Camera error: {e}")

    return router
