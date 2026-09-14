from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import create_router
from backend.logging.logger import RoverLogger
from backend.hardware.factory import get_hardware_gateway
from backend.safety.manager import SafetyManager
from backend.services.rover_state import RoverStateManager
from backend.websocket.manager import WebSocketManager
from backend.autonomy.engine import AutonomyEngine
from backend.services.camera_service import CameraService
from backend.services.vision.service import VisionService
from backend.services.aesa_engine import AESAEngine
from backend.services.storage_service import StorageService
from backend.services.mission_manager import MissionManager

# ─────────────────────────────────────────────────────────────
# Shared Service Singletons
# ─────────────────────────────────────────────────────────────
rover_state = RoverStateManager()
websocket_manager = WebSocketManager()
logger = RoverLogger()

safety_manager = SafetyManager(
    rover_state=rover_state,
)

hardware_gateway = get_hardware_gateway(
    rover_state=rover_state,
    websocket_manager=websocket_manager,
)

autonomy_engine = AutonomyEngine(
    rover_state=rover_state,
    gateway=hardware_gateway,
    websocket_manager=websocket_manager
)

# AESAR Intelligence Subsystems
camera_service = CameraService()
vision_service = VisionService()
aesa_engine = AESAEngine()
storage_service = StorageService()
mission_manager = MissionManager(
    rover_state=rover_state,
    camera_service=camera_service,
    vision_service=vision_service,
    aesa_engine=aesa_engine,
    storage_service=storage_service,
    websocket_manager=websocket_manager,
    hardware_gateway=hardware_gateway,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("ARACHNID backend starting up")
    await hardware_gateway.start()
    logger.info(f"Hardware gateway ({hardware_gateway.__class__.__name__}) started")
    await autonomy_engine.start()

    yield

    logger.info("ARACHNID backend shutting down")
    camera_service.release()
    await autonomy_engine.stop()
    await hardware_gateway.stop()
    logger.info("Hardware gateway stopped cleanly")


app = FastAPI(
    title="ARACHNID Rover Backend",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    create_router(
        rover_state=rover_state,
        safety_manager=safety_manager,
        logger=logger,
        hardware_gateway=hardware_gateway,
        autonomy_engine=autonomy_engine,
        camera_service=camera_service,
        vision_service=vision_service,
        aesa_engine=aesa_engine,
        storage_service=storage_service,
        mission_manager=mission_manager,
    )
)


@app.websocket("/ws")
@app.websocket("/ws/robot")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket_manager.connect(websocket)
    logger.info("WebSocket client connected")

    try:
        while True:
            try:
                # Wait for any incoming client message (keepalive/ping/requests)
                await websocket.receive_text()
            except (WebSocketDisconnect, RuntimeError):
                break
    finally:
        await websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")