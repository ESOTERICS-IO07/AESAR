from __future__ import annotations

import pytest
from backend.models.schemas import CameraConfigRequest, CameraState
from backend.services.camera_service import CameraService, SimulatedCameraProvider


@pytest.mark.asyncio
async def test_simulated_camera_provider():
    provider = SimulatedCameraProvider()
    frame = await provider.capture_frame(station_id=1)
    assert isinstance(frame, bytes)
    assert len(frame) > 100
    # Check JPEG header 0xFF 0xD8
    assert frame[:2] == b"\xff\xd8"


@pytest.mark.asyncio
async def test_camera_service_snapshot():
    service = CameraService()
    frame = await service.capture_snapshot(station_id=2)
    assert isinstance(frame, bytes)
    assert len(frame) > 100
    status = service.get_status()
    assert status.state in (CameraState.READY, CameraState.ONLINE)


@pytest.mark.asyncio
async def test_camera_service_update_config():
    service = CameraService()
    new_cfg = CameraConfigRequest(
        stream_url="http://192.168.1.50:8080/video",
        snapshot_url="http://192.168.1.50:8080/shot.jpg",
        enabled=True,
    )
    status = service.update_config(new_cfg)
    assert status.stream_url == "http://192.168.1.50:8080/video"
    assert status.snapshot_url == "http://192.168.1.50:8080/shot.jpg"
