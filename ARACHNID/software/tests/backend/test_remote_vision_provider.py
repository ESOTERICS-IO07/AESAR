from __future__ import annotations

import io
import time
from typing import Any, Dict
import httpx
from PIL import Image
import pytest

from backend.config.settings import settings
from backend.models.schemas import VisionDetection, VisionResult, VisionStatus
from backend.services.vision.classes import (
    ALL_CANONICAL_CLASSES,
    CANONICAL_DEFENDERS,
    CANONICAL_PESTS,
)
from backend.services.vision.mock_provider import MockVisionProvider
from backend.services.vision.remote_provider import RemoteVisionProvider
from backend.services.vision.service import VisionService
from backend.services.vision.yolo_provider import YOLOVisionProvider


def _get_valid_test_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), color=(34, 139, 34)).save(buf, format="JPEG")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
# 1. Valid Detections & Canonical Class Adaptation
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_valid_detections():
    """Verify that remote detections are adapted into canonical VisionResult without image byte transfer."""
    now = time.time()
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ai/status":
            return httpx.Response(
                200,
                json={
                    "state": "ai_ready",
                    "inference_fps": 18.5,
                    "updated_at": now - 0.2,  # Fresh observation (200ms old)
                    "detections": [
                        {
                            "class_name": "aphids",  # Alias for cotton_aphids
                            "category": "pest",
                            "confidence": 0.89,
                            "count": 3,
                            "bounding_box": [10, 10, 50, 50],
                        },
                        {
                            "class_name": "ladybird",  # Alias for ladybird_beetle
                            "category": "defender",
                            "confidence": 0.94,
                            "count": 1,
                            "bounding_box": [100, 120, 140, 160],
                        },
                    ],
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg(), station_id=2, view="middle")

    assert result.status == VisionStatus.SUCCESS
    assert result.station_id == 2
    assert result.provider == "remote"
    assert len(result.detections) == 2

    # Verify canonical pest
    pests = result.pests
    assert len(pests) == 1
    assert pests[0].name == "cotton_aphids"
    assert pests[0].count == 3
    assert pests[0].confidence == 0.89

    # Verify canonical defender
    defenders = result.defenders
    assert len(defenders) == 1
    assert defenders[0].name == "ladybird_beetle"
    assert defenders[0].count == 1
    assert defenders[0].confidence == 0.94

    # Verify evidence URL link in image_metadata (NO image byte transfer)
    assert result.image_metadata is not None
    assert result.image_metadata.get("evidence_url") == "http://machine2:8001/api/ai/annotated"
    assert result.image_metadata.get("stream_url") == "http://machine2:8001/api/stream"


# ─────────────────────────────────────────────────────────────
# 2. Empty Detections
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_empty_detections():
    """Verify that empty remote detection list yields NO_DETECTIONS status."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ai/status":
            return httpx.Response(
                200,
                json={
                    "state": "ai_ready",
                    "inference_fps": 20.0,
                    "updated_at": time.time(),
                    "detections": [],
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg(), station_id=1)
    assert result.status == VisionStatus.NO_DETECTIONS
    assert len(result.detections) == 0
    assert len(result.pests) == 0
    assert len(result.defenders) == 0


# ─────────────────────────────────────────────────────────────
# 3. Non-Canonical Class Rejection & Filtering
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_non_canonical_classes():
    """Verify that non-canonical classes are safely rejected while preserving canonical ones."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ai/status":
            return httpx.Response(
                200,
                json={
                    "state": "ai_ready",
                    "updated_at": time.time(),
                    "detections": [
                        {"class_name": "BPH", "confidence": 0.85, "count": 2},
                        {"class_name": "alien_insect", "confidence": 0.99, "count": 5},
                        {"class_name": "tractor", "confidence": 0.70, "count": 1},
                    ],
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.SUCCESS
    assert len(result.detections) == 1
    assert result.detections[0].class_name == "brown_planthopper"


# ─────────────────────────────────────────────────────────────
# 4. Model Loading State
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_model_loading():
    """Verify MODEL_NOT_CONFIGURED when remote model is still loading."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"state": "model_loading", "detail": "Loading weights..."})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.MODEL_NOT_CONFIGURED
    assert len(result.detections) == 0
    assert "Loading weights..." in (result.error_message or "")


# ─────────────────────────────────────────────────────────────
# 5. Model Unavailable State
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_model_unavailable():
    """Verify MODEL_NOT_CONFIGURED when remote YOLO model is not configured."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"state": "model_unavailable", "detail": "Model file not found"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.MODEL_NOT_CONFIGURED
    assert len(result.detections) == 0
    assert "Model file not found" in (result.error_message or "")


# ─────────────────────────────────────────────────────────────
# 6. Inference Error State
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_inference_error():
    """Verify INFERENCE_FAILURE when remote service reports inference error."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"state": "inference_error", "detail": "CUDA out of memory"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.INFERENCE_FAILURE
    assert len(result.detections) == 0
    assert "CUDA out of memory" in (result.error_message or "")


# ─────────────────────────────────────────────────────────────
# 7. Connection Failure (Honest Error)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_connection_failure():
    """Verify IMAGE_UNAVAILABLE and honest error when remote host is unreachable."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Connection refused by target machine")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg(), station_id=4)
    assert result.status == VisionStatus.IMAGE_UNAVAILABLE
    assert result.station_id == 4
    assert len(result.detections) == 0
    assert "unreachable" in (result.error_message or "").lower()


# ─────────────────────────────────────────────────────────────
# 8. Timeout
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_timeout():
    """Verify IMAGE_UNAVAILABLE when remote call times out."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Request timed out after 4.0s")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.IMAGE_UNAVAILABLE
    assert len(result.detections) == 0


# ─────────────────────────────────────────────────────────────
# 9. HTTP Error (e.g. 500 Server Error)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_http_error():
    """Verify INFERENCE_FAILURE on HTTP 500 response from remote."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.INFERENCE_FAILURE
    assert len(result.detections) == 0
    assert "500" in (result.error_message or "")


# ─────────────────────────────────────────────────────────────
# 10. Malformed JSON
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_malformed_json():
    """Verify INFERENCE_FAILURE when remote response is not valid JSON."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>Bad Gateway or HTML body</body></html>")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg())
    assert result.status == VisionStatus.INFERENCE_FAILURE
    assert len(result.detections) == 0


# ─────────────────────────────────────────────────────────────
# 11. Stale updated_at
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_stale_updated_at():
    """Verify IMAGE_UNAVAILABLE when remote observation updated_at is excessively stale."""
    stale_timestamp = time.time() - 30.0  # 30 seconds ago (max allowed is 5.0s)
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ai/status":
            return httpx.Response(
                200,
                json={
                    "state": "ai_ready",
                    "inference_fps": 10.0,
                    "updated_at": stale_timestamp,
                    "detections": [
                        {"class_name": "aphids", "confidence": 0.88, "count": 1}
                    ],
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = RemoteVisionProvider(base_url="http://machine2:8001", max_staleness_seconds=5.0, client=client)

    result = await provider.analyze_image(_get_valid_test_jpeg(), station_id=3)
    assert result.status == VisionStatus.IMAGE_UNAVAILABLE
    assert len(result.detections) == 0
    assert "stale" in (result.error_message or "").lower()
    assert result.image_metadata is not None
    assert result.image_metadata.get("stale") is True


# ─────────────────────────────────────────────────────────────
# 12. Health Check (Connected, Disconnected, Unreachable)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remote_provider_health_check():
    """Verify health check returns True only when remote camera reports connected."""
    # Scenario A: Connected
    def handler_connected(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/status":
            return httpx.Response(200, json={"connected": True, "fps": 25.0, "source_kind": "ip"})
        return httpx.Response(404)

    client_conn = httpx.AsyncClient(transport=httpx.MockTransport(handler_connected))
    prov_conn = RemoteVisionProvider(base_url="http://machine2:8001", client=client_conn)
    assert await prov_conn.check_health() is True

    # Scenario B: Disconnected
    def handler_disconnected(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/status":
            return httpx.Response(200, json={"connected": False, "error": "Camera offline"})
        return httpx.Response(404)

    client_disconn = httpx.AsyncClient(transport=httpx.MockTransport(handler_disconnected))
    prov_disconn = RemoteVisionProvider(base_url="http://machine2:8001", client=client_disconn)
    assert await prov_disconn.check_health() is False

    # Scenario C: Unreachable
    def handler_unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("Unreachable")

    client_unreachable = httpx.AsyncClient(transport=httpx.MockTransport(handler_unreachable))
    prov_unreachable = RemoteVisionProvider(base_url="http://machine2:8001", client=client_unreachable)
    assert await prov_unreachable.check_health() is False


# ─────────────────────────────────────────────────────────────
# 13. Provider Dispatch (DEMO vs LIVE with provider=remote)
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vision_service_provider_dispatch(monkeypatch):
    """Verify VisionService selects appropriate provider based on mode and settings."""
    # 1. In DEMO mode, must always use MockVisionProvider
    monkeypatch.setattr(settings, "aesar_mode", "DEMO")
    service_demo = VisionService()
    assert isinstance(service_demo.get_active_provider(), MockVisionProvider)

    # 2. In LIVE mode with vision_provider="remote", must use RemoteVisionProvider
    monkeypatch.setattr(settings, "aesar_mode", "LIVE")
    monkeypatch.setattr(settings, "vision_provider", "remote")
    service_remote = VisionService()
    assert isinstance(service_remote.get_active_provider(), RemoteVisionProvider)
    assert service_remote.is_model_configured() is True

    # 3. In LIVE mode with vision_provider="yolo", must use YOLOVisionProvider
    monkeypatch.setattr(settings, "vision_provider", "yolo")
    service_yolo = VisionService()
    assert isinstance(service_yolo.get_active_provider(), YOLOVisionProvider)

    # 4. Mode switching at runtime
    service_yolo.set_mode("DEMO")
    assert isinstance(service_yolo.get_active_provider(), MockVisionProvider)

    monkeypatch.setattr(settings, "vision_provider", "remote")
    service_yolo.set_mode("LIVE")
    assert isinstance(service_yolo.get_active_provider(), RemoteVisionProvider)

    # 5. Full frame analysis through VisionService with remote provider
    now = time.time()
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/ai/status":
            return httpx.Response(
                200,
                json={
                    "state": "ai_ready",
                    "updated_at": now,
                    "detections": [
                        {"class_name": "green_leafhopper", "confidence": 0.81, "count": 1}
                    ],
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service_yolo.remote_provider = RemoteVisionProvider(base_url="http://machine2:8001", client=client)
    service_yolo.set_mode("LIVE")  # Points to remote_provider

    res = await service_yolo.analyze_frame(_get_valid_test_jpeg(), station_id=5, view="upper")
    assert res.status == VisionStatus.SUCCESS
    assert res.station_id == 5
    assert res.view == "upper"
    assert len(res.detections) == 1
    assert res.detections[0].class_name == "green_leafhopper"
    assert res.image_metadata is not None
    assert res.image_metadata.get("evidence_url") == "http://machine2:8001/api/ai/annotated"
