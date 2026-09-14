from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter

from backend.config.settings import settings
from backend.models.schemas import (
    AesarModeRequest,
    AesarModeResponse,
    AgriSensorState,
    EnvironmentData,
)

router = APIRouter(tags=["environmental"])


def create_agri_router(rover_state: Any, vision_service: Any = None) -> APIRouter:
    """Creates router for environmental sensing and operational mode management."""

    @router.get("/environment/current", response_model=EnvironmentData)
    async def get_current_environment() -> EnvironmentData:
        telemetry = None
        if hasattr(rover_state, "get_telemetry"):
            telemetry = rover_state.get_telemetry()

        if telemetry and telemetry.environment:
            return telemetry.environment

        # If in DEMO mode or sensors not ready yet
        if settings.aesar_mode.upper() == "DEMO":
            return EnvironmentData(
                temperature_c=24.8,
                humidity_percent=63.5,
                soil_moisture_raw=2250,
                soil_moisture_percent=52.8,
                timestamp=time.time(),
                available=True,
                status=AgriSensorState.AVAILABLE,
            )

        return EnvironmentData(
            temperature_c=None,
            humidity_percent=None,
            soil_moisture_raw=None,
            soil_moisture_percent=None,
            timestamp=None,
            available=False,
            status=AgriSensorState.UNAVAILABLE,
        )

    @router.get("/environment/calibration")
    async def get_calibration_config() -> Dict[str, Any]:
        return {
            "dht22": {
                "temp_min_c": settings.environmental_dht22_temp_min_c,
                "temp_max_c": settings.environmental_dht22_temp_max_c,
                "humidity_min_percent": settings.environmental_dht22_humidity_min_percent,
                "humidity_max_percent": settings.environmental_dht22_humidity_max_percent,
            },
            "soil_moisture": {
                "dry_adc": settings.environmental_soil_dry_adc,
                "wet_adc": settings.environmental_soil_wet_adc,
                "invert": settings.environmental_soil_invert,
                "min_adc": settings.environmental_soil_min_adc,
                "max_adc": settings.environmental_soil_max_adc,
            },
        }

    @router.get("/mode", response_model=AesarModeResponse)
    async def get_aesar_mode() -> AesarModeResponse:
        return AesarModeResponse(mode=settings.aesar_mode.upper())

    @router.post("/mode", response_model=AesarModeResponse)
    async def set_aesar_mode(request: AesarModeRequest) -> AesarModeResponse:
        target_mode = request.mode.upper()
        if target_mode not in ("LIVE", "DEMO"):
            target_mode = "DEMO"

        settings.aesar_mode = target_mode
        if vision_service and hasattr(vision_service, "set_mode"):
            vision_service.set_mode(target_mode)

        return AesarModeResponse(mode=settings.aesar_mode)

    return router
