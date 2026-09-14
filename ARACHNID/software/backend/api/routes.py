from __future__ import annotations

import inspect
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    CommandRequest,
    CommandResponse,
    EmergencyStopResponse,
    ExplorationData,
    HealthResponse,
    LogsResponse,
    MapData,
    ModeRequest,
    ModeResponse,
    NavigationData,
    Point2D,
    RoverStatus,
    StopResponse,
    Telemetry,
)


from backend.api.routes_agri import create_agri_router
from backend.api.routes_camera import create_camera_router
from backend.api.routes_vision import create_vision_router
from backend.api.routes_aesa import create_aesa_router
from backend.api.routes_mission import create_mission_router
from backend.api.routes_history import create_history_router


def create_router(
    rover_state: Any,
    safety_manager: Any,
    logger: Any,
    hardware_gateway: Any,
    autonomy_engine: Any = None,
    camera_service: Any = None,
    vision_service: Any = None,
    aesa_engine: Any = None,
    storage_service: Any = None,
    mission_manager: Any = None,
) -> APIRouter:
    """
    Create the ARACHNID REST API router.

    Injected dependencies from backend.main ensure a single shared instance
    across state, safety, logger, and hardware gateway services.
    """
    router = APIRouter(prefix="/api")

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        is_connected = True
        if hasattr(rover_state, "get_status"):
            status = rover_state.get_status()
            is_connected = status.connected if hasattr(status, "connected") else True

        return HealthResponse(
            status="ok",
            backend=True,
            hardware_connected=is_connected,
        )

    # ------------------------------------------------------------------
    # Rover status
    # ------------------------------------------------------------------
    @router.get("/rover/status", response_model=RoverStatus)
    async def get_rover_status() -> Any:
        if hasattr(rover_state, "get_status"):
            return rover_state.get_status()
        return RoverStatus()

    # ------------------------------------------------------------------
    # Rover telemetry
    # ------------------------------------------------------------------
    @router.get("/rover/telemetry", response_model=Telemetry)
    async def get_rover_telemetry() -> Any:
        telemetry = None
        if hasattr(rover_state, "get_telemetry"):
            telemetry = rover_state.get_telemetry()

        if telemetry is None and hasattr(hardware_gateway, "get_telemetry"):
            telemetry = hardware_gateway.get_telemetry()

        if telemetry is None:
            telemetry = Telemetry()

        return telemetry

    # ------------------------------------------------------------------
    # Rover mode
    # ------------------------------------------------------------------
    @router.post("/rover/mode", response_model=ModeResponse)
    async def set_rover_mode(request: ModeRequest) -> ModeResponse:
        mode = request.mode

        if hasattr(rover_state, "is_emergency_stopped") and rover_state.is_emergency_stopped():
            raise HTTPException(
                status_code=409,
                detail="Cannot change rover mode while in EMERGENCY_STOP state",
            )

        if hasattr(safety_manager, "validate_mode_change"):
            try:
                safety_manager.validate_mode_change()
            except RuntimeError as exc:
                raise HTTPException(status_code=409, detail=str(exc))

        if hasattr(rover_state, "set_mode"):
            success = rover_state.set_mode(mode)
            if success is False:
                raise HTTPException(
                    status_code=409,
                    detail="Unable to change rover mode",
                )

        logger.info(f"Rover mode updated to {mode}")
        return ModeResponse(success=True, mode=mode)

    # ------------------------------------------------------------------
    # Rover command
    # ------------------------------------------------------------------
    @router.post("/rover/command", response_model=CommandResponse)
    async def rover_command(request: CommandRequest) -> CommandResponse:
        # Check safety & emergency stop condition
        if hasattr(safety_manager, "validate_velocity_command"):
            try:
                safety_manager.validate_velocity_command(request)
            except RuntimeError as exc:
                raise HTTPException(status_code=409, detail=str(exc))
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc))

        if hasattr(safety_manager, "can_accept_command"):
            if not safety_manager.can_accept_command():
                raise HTTPException(
                    status_code=409,
                    detail="Rover is in EMERGENCY_STOP state and cannot accept commands",
                )

        command_dict = request.model_dump()
        if hasattr(hardware_gateway, "send_command"):
            res = hardware_gateway.send_command(command_dict)
            if inspect.isawaitable(res):
                await res

        logger.info(f"Velocity command accepted: {request.command_id}")
        return CommandResponse(success=True, command_id=request.command_id)

    # ------------------------------------------------------------------
    # Normal stop
    # ------------------------------------------------------------------
    @router.post("/rover/stop", response_model=StopResponse)
    async def rover_stop() -> StopResponse:
        if hasattr(safety_manager, "stop"):
            res = safety_manager.stop()
            if inspect.isawaitable(res):
                await res
        elif hasattr(rover_state, "stop"):
            rover_state.stop()

        if hasattr(hardware_gateway, "stop_rover"):
            res = hardware_gateway.stop_rover()
            if inspect.isawaitable(res):
                await res

        logger.info("Rover normal stop requested")
        return StopResponse(success=True, stopped=True)

    # ------------------------------------------------------------------
    # Emergency stop
    # ------------------------------------------------------------------
    @router.post("/rover/emergency-stop", response_model=EmergencyStopResponse)
    async def emergency_stop() -> EmergencyStopResponse:
        if hasattr(safety_manager, "emergency_stop"):
            res = safety_manager.emergency_stop()
            if inspect.isawaitable(res):
                await res
        elif hasattr(rover_state, "emergency_stop"):
            rover_state.emergency_stop()

        if hasattr(hardware_gateway, "emergency_stop"):
            res = hardware_gateway.emergency_stop()
            if inspect.isawaitable(res):
                await res

        logger.warning("Emergency stop activated")
        return EmergencyStopResponse(success=True, emergency_stop=True)

    # ------------------------------------------------------------------
    # Reset emergency stop
    # ------------------------------------------------------------------
    @router.post("/rover/emergency-stop/reset", response_model=EmergencyStopResponse)
    async def reset_emergency_stop() -> EmergencyStopResponse:
        if hasattr(safety_manager, "reset_emergency_stop"):
            res = safety_manager.reset_emergency_stop()
            if inspect.isawaitable(res):
                await res
        elif hasattr(rover_state, "reset_emergency_stop"):
            rover_state.reset_emergency_stop()

        if hasattr(hardware_gateway, "reset_emergency_stop"):
            res = hardware_gateway.reset_emergency_stop()
            if inspect.isawaitable(res):
                await res

        logger.info("Emergency stop reset")
        return EmergencyStopResponse(success=True, emergency_stop=False)

    # ------------------------------------------------------------------
    # Map
    # ------------------------------------------------------------------
    @router.get("/map", response_model=MapData)
    async def get_map() -> Any:
        if autonomy_engine and hasattr(autonomy_engine, "mapper"):
            return autonomy_engine.mapper.get_map_data()
        return MapData()

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    @router.get("/navigation", response_model=NavigationData)
    async def get_navigation() -> Any:
        if autonomy_engine:
            return NavigationData(
                status="NAVIGATING" if autonomy_engine._current_path else "IDLE",
                goal=autonomy_engine._current_goal,
                path=[Point2D(x=p[0], y=p[1]) for p in autonomy_engine._current_path]
            )
        return NavigationData()

    # ------------------------------------------------------------------
    # Exploration
    # ------------------------------------------------------------------
    @router.get("/exploration", response_model=ExplorationData)
    async def get_exploration() -> Any:
        if autonomy_engine:
            frontiers = autonomy_engine.explorer.find_frontiers()
            return ExplorationData(
                status="EXPLORING" if autonomy_engine._current_goal else "IDLE",
                explored_percent=0.0,
                frontier_count=len(frontiers),
                current_goal=autonomy_engine._current_goal
            )
        return ExplorationData()

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------
    @router.get("/logs", response_model=LogsResponse)
    async def get_logs() -> LogsResponse:
        logs_list = []
        if hasattr(logger, "get_logs"):
            logs_list = logger.get_logs()
        return LogsResponse(logs=logs_list)

    # ------------------------------------------------------------------
    # AESAR Sub-routers
    # ------------------------------------------------------------------
    router.include_router(create_agri_router(rover_state=rover_state, vision_service=vision_service))
    if camera_service is not None:
        router.include_router(create_camera_router(camera_service))
    if vision_service is not None and camera_service is not None:
        router.include_router(create_vision_router(vision_service, camera_service))
    if aesa_engine is not None:
        router.include_router(create_aesa_router(aesa_engine))
    if mission_manager is not None:
        router.include_router(create_mission_router(mission_manager))
    if storage_service is not None:
        router.include_router(create_history_router(storage_service))

    return router