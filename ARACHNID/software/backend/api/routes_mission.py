from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    MissionPlan,
    MissionStatusResponse,
    StationObservationRecord,
)
from backend.services.mission_manager import MissionManager

logger = logging.getLogger("aesar.api.mission")

router = APIRouter(prefix="/mission", tags=["mission"])


def create_mission_router(mission_manager: MissionManager) -> APIRouter:
    """Creates router for agricultural scouting mission lifecycle."""

    @router.get("/status", response_model=MissionStatusResponse)
    async def get_mission_status() -> MissionStatusResponse:
        return mission_manager.get_status()

    @router.post("/start", response_model=MissionStatusResponse)
    async def start_mission(plan: Optional[MissionPlan] = None) -> MissionStatusResponse:
        try:
            return await mission_manager.start_mission(plan)
        except Exception as e:
            logger.error(f"Failed to start mission: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/pause", response_model=MissionStatusResponse)
    async def pause_mission() -> MissionStatusResponse:
        return mission_manager.pause_mission()

    @router.post("/resume", response_model=MissionStatusResponse)
    async def resume_mission() -> MissionStatusResponse:
        return mission_manager.resume_mission()

    @router.post("/abort", response_model=MissionStatusResponse)
    async def abort_mission() -> MissionStatusResponse:
        return await mission_manager.abort_mission()

    @router.post("/analyze-current", response_model=StationObservationRecord)
    async def analyze_current_station() -> StationObservationRecord:
        try:
            return await mission_manager.analyze_current_station()
        except Exception as e:
            logger.error(f"Failed to analyze current station: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
