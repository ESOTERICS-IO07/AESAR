from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from backend.config.settings import settings
from backend.models.schemas import (
    AgriSensorState,
    EnvironmentData,
    FieldAssessment,
    MissionPlan,
    MissionState,
    MissionStatusResponse,
    SamplingStation,
    StationObservationRecord,
)
from backend.services.aesa_engine import AESAEngine
from backend.services.camera_service import CameraService
from backend.services.rover_state import RoverStateManager
from backend.services.storage_service import StorageService
from backend.services.vision.service import VisionService
from backend.websocket.manager import WebSocketManager

logger = logging.getLogger("aesar.mission")

DEFAULT_DEMO_STATIONS = [
    SamplingStation(id=1, x=0.8, y=0.8, name="Row 1 - North Terminal"),
    SamplingStation(id=2, x=1.6, y=0.8, name="Row 1 - Mid Ridge"),
    SamplingStation(id=3, x=2.4, y=0.8, name="Row 1 - South Terminal"),
    SamplingStation(id=4, x=2.8, y=1.5, name="Turnaround Alley"),
    SamplingStation(id=5, x=2.4, y=2.2, name="Row 2 - South Terminal"),
    SamplingStation(id=6, x=1.6, y=2.2, name="Row 2 - Mid Ridge"),
    SamplingStation(id=7, x=0.8, y=2.2, name="Row 2 - North Terminal"),
    SamplingStation(id=8, x=0.5, y=1.5, name="Border Hedgerow"),
    SamplingStation(id=9, x=1.3, y=1.5, name="Central Canopy A"),
    SamplingStation(id=10, x=2.0, y=1.5, name="Central Canopy B"),
]


class MissionManager:
    """
    Agricultural Mission Controller for AESAR.
    Implements a 15-state scouting lifecycle across an arbitrary number of stations.
    Orchestrates point-to-point motion, stabilization, frame capture, sensor read,
    vision inference, deterministic AESA calculation, and live WebSocket streaming.
    """

    def __init__(
        self,
        rover_state: RoverStateManager,
        camera_service: CameraService,
        vision_service: VisionService,
        aesa_engine: AESAEngine,
        storage_service: StorageService,
        websocket_manager: WebSocketManager,
        hardware_gateway: Optional[Any] = None,
    ) -> None:
        self.rover_state = rover_state
        self.camera_service = camera_service
        self.vision_service = vision_service
        self.aesa_engine = aesa_engine
        self.storage_service = storage_service
        self.websocket_manager = websocket_manager
        self.hardware_gateway = hardware_gateway

        self.current_state = MissionState.IDLE
        self.current_mission_id: Optional[str] = None
        self.stations: List[SamplingStation] = []
        self.current_station_index: int = 0
        self.observations: List[StationObservationRecord] = []
        self.field_assessment: Optional[FieldAssessment] = None

        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Unpaused initially
        self._abort_requested = False
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._error_message: Optional[str] = None

    def get_status(self) -> MissionStatusResponse:
        current_station = None
        if 0 <= self.current_station_index < len(self.stations):
            current_station = self.stations[self.current_station_index]

        completed_count = len(self.observations)
        remaining_count = max(0, len(self.stations) - completed_count)

        return MissionStatusResponse(
            mission_id=self.current_mission_id,
            state=self.current_state,
            current_station=current_station,
            current_station_index=self.current_station_index,
            total_stations=len(self.stations),
            completed_stations=completed_count,
            remaining_stations=remaining_count,
            observations=self.observations,
            field_assessment=self.field_assessment,
            start_time=self._start_time,
            end_time=self._end_time,
            error_message=self._error_message,
        )

    async def _broadcast_status(self) -> None:
        now_ms = int(time.time() * 1000)
        try:
            status_data = self.get_status().model_dump()
            await self.websocket_manager.broadcast("mission_status", now_ms, status_data)
        except Exception as e:
            logger.error(f"Failed to broadcast mission status: {e}")

    async def start_mission(self, plan: Optional[MissionPlan] = None) -> MissionStatusResponse:
        if self.current_state not in (MissionState.IDLE, MissionState.COMPLETED, MissionState.ABORTED, MissionState.ERROR):
            raise RuntimeError(f"Cannot start mission while in state {self.current_state}")

        mission_id = f"AESAR-{int(time.time())}"
        self.current_mission_id = mission_id
        self._start_time = time.time()
        self._end_time = None
        self._error_message = None
        self._abort_requested = False
        self._pause_event.set()
        self.observations = []
        self.field_assessment = None
        self.current_station_index = 0

        # Load stations
        if plan and plan.stations:
            self.stations = plan.stations
        else:
            self.stations = list(DEFAULT_DEMO_STATIONS)

        self.storage_service.create_mission(self.current_mission_id, len(self.stations))
        self.current_state = MissionState.INITIALIZING
        await self._broadcast_status()

        self._task = asyncio.create_task(self._run_mission_loop())
        return self.get_status()

    def pause_mission(self) -> MissionStatusResponse:
        if self._task and not self._task.done():
            self._pause_event.clear()
            logger.info("Mission paused by operator")
        return self.get_status()

    def resume_mission(self) -> MissionStatusResponse:
        if self._task and not self._task.done():
            self._pause_event.set()
            logger.info("Mission resumed by operator")
        return self.get_status()

    async def abort_mission(self) -> MissionStatusResponse:
        self._abort_requested = True
        self._pause_event.set()  # Unblock if waiting
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        if self.hardware_gateway:
            await self.hardware_gateway.stop_rover()

        self.current_state = MissionState.ABORTED
        self._end_time = time.time()
        if self.current_mission_id:
            self.storage_service.update_mission_status(
                self.current_mission_id,
                "ABORTED",
                completed_stations=len(self.observations),
                end_time=self._end_time,
            )
        await self._broadcast_status()
        logger.warning("Mission aborted by operator")
        return self.get_status()

    async def _run_mission_loop(self) -> None:
        try:
            logger.info(f"Starting scouting execution for mission {self.current_mission_id} ({len(self.stations)} stations)")

            for idx, station in enumerate(self.stations):
                self.current_station_index = idx
                await self._pause_event.wait()
                if self._abort_requested or self.rover_state.is_emergency_stopped():
                    break

                # 1. NAVIGATING
                self.current_state = MissionState.NAVIGATING
                await self._broadcast_status()
                await self._navigate_to_station(station)

                # 2. ARRIVED_AT_STATION
                self.current_state = MissionState.ARRIVED_AT_STATION
                await self._broadcast_status()
                if self.hardware_gateway:
                    await self.hardware_gateway.stop_rover()
                await asyncio.sleep(0.3)

                # 3. STABILIZING (1.0s)
                self.current_state = MissionState.STABILIZING
                await self._broadcast_status()
                await asyncio.sleep(1.0)

                # 4. CAPTURING_IMAGE
                self.current_state = MissionState.CAPTURING_IMAGE
                await self._broadcast_status()
                frame_bytes: Optional[bytes] = None
                try:
                    frame_bytes = await self.camera_service.capture_snapshot(station_id=station.id)
                except Exception as e:
                    logger.warning(f"Failed to capture frame at station {station.id}: {e}")

                # 5. READING_SENSORS
                self.current_state = MissionState.READING_SENSORS
                await self._broadcast_status()
                env_data = self._read_environmental_sensors()

                # 6. ANALYZING_IMAGE
                self.current_state = MissionState.ANALYZING_IMAGE
                await self._broadcast_status()
                vision_result = None
                if frame_bytes:
                    try:
                        vision_result = await self.vision_service.analyze_frame(frame_bytes, station_id=station.id)
                    except Exception as e:
                        logger.error(f"Vision analysis failed for station {station.id}: {e}")

                # 7. FUSING_DATA (AESA Engine)
                self.current_state = MissionState.FUSING_DATA
                await self._broadcast_status()
                aesa_analysis = self.aesa_engine.evaluate_station(
                    station_id=station.id,
                    vision=vision_result,
                    env=env_data,
                )

                # 8. STORING_RESULT
                self.current_state = MissionState.STORING_RESULT
                obs_record = StationObservationRecord(
                    station=station,
                    timestamp=time.time(),
                    environment=env_data,
                    vision=vision_result,
                    analysis=aesa_analysis,
                    image_path=None,
                )
                persisted_obs = self.storage_service.save_station_observation(
                    self.current_mission_id,
                    obs_record,
                    image_bytes=frame_bytes,
                )
                self.observations.append(persisted_obs)
                self.storage_service.update_mission_status(
                    self.current_mission_id,
                    "RUNNING",
                    completed_stations=len(self.observations),
                )

                # Broadcast station completion
                now_ms = int(time.time() * 1000)
                await self.websocket_manager.broadcast("station_completed", now_ms, persisted_obs.model_dump())
                await self.websocket_manager.broadcast("aesa_update", now_ms, aesa_analysis.model_dump())
                await self._broadcast_status()

                # 9. MOVING_TO_NEXT_STATION
                if idx < len(self.stations) - 1:
                    self.current_state = MissionState.MOVING_TO_NEXT_STATION
                    await self._broadcast_status()
                    await asyncio.sleep(0.5)

            # 10. FINALIZING
            self.current_state = MissionState.FINALIZING
            await self._broadcast_status()
            self.field_assessment = self.aesa_engine.generate_field_assessment(
                self.current_mission_id,
                self.observations,
            )
            self.storage_service.save_field_assessment(self.field_assessment)
            self._end_time = time.time()
            self.storage_service.update_mission_status(
                self.current_mission_id,
                "COMPLETED",
                completed_stations=len(self.observations),
                end_time=self._end_time,
            )

            # 11. COMPLETED
            self.current_state = MissionState.COMPLETED
            now_ms = int(time.time() * 1000)
            await self.websocket_manager.broadcast("field_card_generated", now_ms, self.field_assessment.model_dump())
            await self._broadcast_status()
            logger.info(f"Mission {self.current_mission_id} completed successfully!")

        except asyncio.CancelledError:
            self.current_state = MissionState.ABORTED
            logger.info("Mission cancelled.")
        except Exception as e:
            logger.exception(f"Unexpected error in mission loop: {e}")
            self.current_state = MissionState.ERROR
            self._error_message = str(e)
            await self._broadcast_status()

    async def _navigate_to_station(self, station: SamplingStation) -> None:
        """
        Navigates the rover towards the station coordinates.
        In DEMO mode, smoothly interpolates rover position across 1.5-2.0s.
        In LIVE mode, sends velocity commands or point goals to gateway.
        """
        curr_x, curr_y, curr_theta = self.rover_state.get_pose()
        steps = 15
        dt = 0.1

        for step in range(1, steps + 1):
            if self._abort_requested or self.rover_state.is_emergency_stopped():
                break

            fraction = step / steps
            interp_x = round(curr_x + (station.x - curr_x) * fraction, 2)
            interp_y = round(curr_y + (station.y - curr_y) * fraction, 2)
            self.rover_state.set_pose(interp_x, interp_y, curr_theta)

            if self.hardware_gateway:
                # In LIVE mode, send slight forward motion target
                await self.hardware_gateway.send_velocity_command(0.15, 0.0)

            await asyncio.sleep(dt)

        # Set final station coordinate
        self.rover_state.set_pose(station.x, station.y, curr_theta)
        if self.hardware_gateway:
            await self.hardware_gateway.stop_rover()

    def _read_environmental_sensors(self) -> EnvironmentData:
        """Extracts environmental telemetry from rover state or returns simulated readings."""
        telemetry = self.rover_state.get_telemetry()
        if telemetry and telemetry.environment:
            return telemetry.environment

        # Fallback if no telemetry packet received yet (e.g. at startup in DEMO)
        return EnvironmentData(
            temperature_c=25.4,
            humidity_percent=62.0,
            soil_moisture_raw=2200,
            soil_moisture_percent=55.5,
            timestamp=time.time(),
            available=True,
            status=AgriSensorState.AVAILABLE,
        )

    async def analyze_current_station(self) -> StationObservationRecord:
        """
        Ad-hoc manual trigger: captures image and analyzes whatever station/position
        the rover is currently at, without running an automated multi-station mission.
        """
        station_id = self.current_station_index + 1
        curr_x, curr_y, _ = self.rover_state.get_pose()
        ad_hoc_station = SamplingStation(
            id=station_id,
            x=round(curr_x, 2),
            y=round(curr_y, 2),
            name=f"Ad-hoc Inspection ({curr_x:.1f}, {curr_y:.1f})",
        )

        mission_id = self.current_mission_id or f"ADHOC-{int(time.time())}"

        # Capture frame
        frame_bytes = await self.camera_service.capture_snapshot(station_id=station_id)
        # Read sensors
        env_data = self._read_environmental_sensors()
        # Analyze vision
        vision_result = await self.vision_service.analyze_frame(frame_bytes, station_id=station_id)
        # AESA Analysis
        aesa_analysis = self.aesa_engine.evaluate_station(
            station_id=station_id,
            vision=vision_result,
            env=env_data,
        )

        obs = StationObservationRecord(
            station=ad_hoc_station,
            timestamp=time.time(),
            environment=env_data,
            vision=vision_result,
            analysis=aesa_analysis,
            image_path=None,
        )

        persisted = self.storage_service.save_station_observation(
            mission_id,
            obs,
            image_bytes=frame_bytes,
        )

        now_ms = int(time.time() * 1000)
        await self.websocket_manager.broadcast("station_completed", now_ms, persisted.model_dump())
        await self.websocket_manager.broadcast("aesa_update", now_ms, aesa_analysis.model_dump())

        return persisted
