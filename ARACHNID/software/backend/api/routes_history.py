from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from backend.models.schemas import FieldAssessment, StationObservationRecord
from backend.services.storage_service import StorageService

logger = logging.getLogger("aesar.api.history")

router = APIRouter(tags=["history"])


def create_history_router(storage_service: StorageService) -> APIRouter:
    """Creates router for historical missions, observation data, and stored images."""

    @router.get("/missions", response_model=List[Dict[str, Any]])
    async def list_missions() -> List[Dict[str, Any]]:
        return storage_service.get_missions()

    @router.get("/missions/{mission_id}", response_model=Dict[str, Any])
    async def get_mission_by_id(mission_id: str) -> Dict[str, Any]:
        m = storage_service.get_mission(mission_id)
        if not m:
            raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")
        return m

    @router.get("/missions/{mission_id}/stations", response_model=List[StationObservationRecord])
    async def get_mission_stations(mission_id: str) -> List[StationObservationRecord]:
        return storage_service.get_station_observations(mission_id)

    @router.get("/missions/{mission_id}/field-card", response_model=FieldAssessment)
    async def get_mission_field_card(mission_id: str) -> FieldAssessment:
        card = storage_service.get_field_assessment(mission_id)
        if not card:
            raise HTTPException(status_code=404, detail=f"Field card not found for mission {mission_id}")
        return card

    @router.get("/images/{filename}")
    async def get_image(filename: str) -> Response:
        filepath = os.path.join(storage_service.images_dir, filename)
        if not os.path.isfile(filepath):
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(filepath, media_type="image/jpeg")

    return router
