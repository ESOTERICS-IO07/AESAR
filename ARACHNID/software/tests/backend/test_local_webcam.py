from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import CameraConfigRequest, CameraState, VisionStatus
from backend.services.camera_service import CameraService, LocalWebcamProvider
from backend.services.vision.service import VisionService


def _make_mock_frame():
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.mark.asyncio
async def test_local_webcam_available():
    provider = LocalWebcamProvider(camera_index=0)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, _make_mock_frame())

    with patch('backend.services.camera_service.cv2.VideoCapture', return_value=mock_cap):
        jpeg_bytes = await provider.capture_frame()
        assert isinstance(jpeg_bytes, bytes)
        assert len(jpeg_bytes) > 50
        assert jpeg_bytes[:2] == b'\xff\xd8'
        mock_cap.read.assert_called()
    provider.release()


@pytest.mark.asyncio
async def test_local_webcam_unavailable():
    provider = LocalWebcamProvider(camera_index=99)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False

    with patch('backend.services.camera_service.cv2.VideoCapture', return_value=mock_cap):
        with pytest.raises((ConnectionError, RuntimeError)):
            await provider.capture_frame()
    provider.release()


@pytest.mark.asyncio
async def test_local_webcam_check_health():
    provider = LocalWebcamProvider(camera_index=0)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    with patch('backend.services.camera_service.cv2.VideoCapture', return_value=mock_cap):
        is_healthy = await provider.check_health()
        assert is_healthy is True

    provider.release()

    mock_fail_cap = MagicMock()
    mock_fail_cap.isOpened.return_value = False
    with patch('backend.services.camera_service.cv2.VideoCapture', return_value=mock_fail_cap):
        is_healthy_fail = await provider.check_health()
        assert is_healthy_fail is False


@pytest.mark.asyncio
async def test_local_webcam_cleanup_release():
    provider = LocalWebcamProvider(camera_index=0)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    provider._cap = mock_cap

    provider.release()
    mock_cap.release.assert_called_once()
    assert provider._cap is None


@pytest.mark.asyncio
async def test_local_webcam_invalid_camera_index():
    provider = LocalWebcamProvider(camera_index=-1)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False

    with patch('backend.services.camera_service.cv2.VideoCapture', return_value=mock_cap):
        with pytest.raises((ConnectionError, RuntimeError)):
            await provider.capture_frame()
    provider.release()


@pytest.mark.asyncio
async def test_camera_service_no_fake_frame_in_live_mode():
    service = CameraService()
    with patch('backend.config.settings.settings.aesar_mode', 'LIVE'):
        service.provider_name = 'local'
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False

        with patch('backend.services.camera_service.cv2.VideoCapture', return_value=mock_cap):
            with pytest.raises(RuntimeError) as exc_info:
                await service.capture_snapshot()
            assert 'Camera unavailable' in str(exc_info.value)
            assert service.get_status().state in (CameraState.CAMERA_UNAVAILABLE, CameraState.ERROR)
            assert service.get_status().connected is False


@pytest.mark.asyncio
async def test_camera_service_update_config_switch_provider():
    service = CameraService()
    req = CameraConfigRequest(provider='local', local_camera_index=1)
    status = service.update_config(req)
    assert status.provider == 'local'
    assert status.camera_index == 1
    assert service.local_provider.camera_index == 1

    req_http = CameraConfigRequest(provider='http', snapshot_url='http://10.0.0.5:8080/shot.jpg')
    status_http = service.update_config(req_http)
    assert status_http.provider == 'http'
    assert status_http.snapshot_url == 'http://10.0.0.5:8080/shot.jpg'


@pytest.mark.asyncio
async def test_captured_jpeg_to_vision_service_mock_mode():
    vision_service = VisionService()
    vision_service.set_mode('DEMO')

    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (320, 240), color=(0, 128, 0)).save(buf, format='JPEG')
    jpeg_bytes = buf.getvalue()

    result = await vision_service.analyze_frame(jpeg_bytes, station_id=1, view='middle')
    assert result.status == VisionStatus.SUCCESS
    assert result.station_id == 1
    assert result.view == 'middle'
    assert len(result.detections) > 0


@pytest.mark.asyncio
async def test_captured_jpeg_to_vision_service_live_model_not_configured():
    vision_service = VisionService()
    vision_service.set_mode('LIVE')

    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (320, 240), color=(0, 128, 0)).save(buf, format='JPEG')
    jpeg_bytes = buf.getvalue()

    result = await vision_service.analyze_frame(jpeg_bytes, station_id=2, view='upper')
    assert result.status == VisionStatus.MODEL_NOT_CONFIGURED
    assert len(result.detections) == 0


def test_api_camera_status():
    with TestClient(app) as client:
        resp = client.get('/api/camera/status')
        assert resp.status_code == 200
        data = resp.json()
        assert 'state' in data
        assert 'provider' in data


def test_api_camera_snapshot():
    with TestClient(app) as client:
        resp = client.get('/api/camera/snapshot')
        assert resp.status_code == 200
        assert resp.headers['content-type'] == 'image/jpeg'
        assert len(resp.content) > 50
