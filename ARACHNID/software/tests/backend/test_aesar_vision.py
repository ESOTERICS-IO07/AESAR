import io
from PIL import Image
import pytest
from backend.models.schemas import PlantHealth
from backend.services.vision.mock_provider import MockVisionProvider
from backend.services.vision.service import VisionService


def _get_valid_test_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color=(34, 139, 34)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_mock_vision_provider_scenarios():
    provider = MockVisionProvider()
    valid_bytes = _get_valid_test_jpeg()

    # Station 1: clean, 0 pests, 3 ladybirds
    res1 = await provider.analyze_image(valid_bytes, station_id=1)
    assert len(res1.pests) == 0
    assert len(res1.defenders) == 1
    assert res1.defenders[0].name in ("ladybird", "ladybird_beetle")
    assert res1.plant_health == PlantHealth.HEALTHY

    # Station 5: severe pest breakout
    res5 = await provider.analyze_image(valid_bytes, station_id=5)
    assert len(res5.pests) >= 2
    assert len(res5.defenders) == 0
    assert res5.plant_health in (PlantHealth.MODERATE_STRESS, PlantHealth.SEVERE_STRESS)


@pytest.mark.asyncio
async def test_vision_service_mock_mode():
    service = VisionService()
    valid_bytes = _get_valid_test_jpeg()
    res = await service.analyze_frame(valid_bytes, station_id=2)
    assert res.overall_confidence > 0.5
    assert len(res.pests) > 0 or len(res.defenders) > 0
