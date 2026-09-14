from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.schemas import (
    AESAStationAnalysis,
    EnvironmentData,
    VisionAnalysisResult,
)
from backend.services.aesa_engine import AESAEngine

logger = logging.getLogger("aesar.api.aesa")

router = APIRouter(prefix="/aesa", tags=["aesa"])


class EvaluateStationRequest(BaseModel):
    station_id: int = 1
    vision: Optional[VisionAnalysisResult] = None
    environment: Optional[EnvironmentData] = None


def create_aesa_router(aesa_engine: AESAEngine) -> APIRouter:
    """Creates router for deterministic AESA calculation engine."""

    @router.post("/evaluate", response_model=AESAStationAnalysis)
    async def evaluate_station(request: EvaluateStationRequest) -> AESAStationAnalysis:
        return aesa_engine.evaluate_station(
            station_id=request.station_id,
            vision=request.vision,
            env=request.environment,
        )

    @router.get("/config")
    async def get_aesa_config() -> Dict[str, Any]:
        return {
            "pest_weights": aesa_engine.pest_weights,
            "defender_weights": aesa_engine.defender_weights,
            "epsilon": aesa_engine.epsilon,
            "thresholds": aesa_engine.thresholds,
        }

    return router
