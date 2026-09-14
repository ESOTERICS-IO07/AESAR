from __future__ import annotations

import base64
import io
import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    CanopyView,
    VisionDetection,
    VisionResult,
    VisionStatus,
)
from backend.services.vision.classes import (
    ALL_CANONICAL_CLASSES,
    CANONICAL_DEFENDERS,
    CANONICAL_PESTS,
    CLASS_TO_CATEGORY,
    get_class_category,
    get_display_name,
    is_valid_vision_class,
    resolve_class_name,
)
from backend.services.vision.mock_provider import MockVisionProvider
from backend.services.vision.preprocessor import ImagePreprocessor, InvalidImageError
from backend.services.vision.service import VisionService
from backend.services.vision.yolo_provider import YOLOVisionProvider


# ─────────────────────────────────────────────────────────────
# 1. Authoritative Classes & Taxonomy Tests
# ─────────────────────────────────────────────────────────────

def test_canonical_classes_count():
    assert len(CANONICAL_PESTS) == 6
    assert len(CANONICAL_DEFENDERS) == 5
    assert len(ALL_CANONICAL_CLASSES) == 11


def test_canonical_class_names():
    expected_pests = {
        "brown_planthopper",
        "green_leafhopper",
        "yellow_stem_borer",
        "cotton_aphids",
        "chilli_thrips",
        "american_bollworm",
    }
    expected_defenders = {
        "ladybird_beetle",
        "lycosa_wolf_spider",
        "mirid_bug",
        "carabid_beetle",
        "green_lacewing",
    }
    assert set(CANONICAL_PESTS) == expected_pests
    assert set(CANONICAL_DEFENDERS) == expected_defenders


def test_alias_resolution():
    assert resolve_class_name("BPH") == "brown_planthopper"
    assert resolve_class_name("GLH") == "green_leafhopper"
    assert resolve_class_name("aphid") == "cotton_aphids"
    assert resolve_class_name("thrip") == "chilli_thrips"
    assert resolve_class_name("ladybug") == "ladybird_beetle"
    assert resolve_class_name("spider") == "lycosa_wolf_spider"
    assert resolve_class_name("ground_beetle") == "carabid_beetle"


def test_class_categories():
    assert get_class_category("cotton_aphids") == "pest"
    assert get_class_category("chilli_thrips") == "pest"
    assert get_class_category("ladybird_beetle") == "defender"
    assert get_class_category("lycosa_wolf_spider") == "defender"


def test_display_names():
    assert get_display_name("brown_planthopper") == "Brown Planthopper (BPH)"
    assert get_display_name("ladybird_beetle") == "Ladybird Beetle adult/larva"


# ─────────────────────────────────────────────────────────────
# 2. Schema Validation Tests
# ─────────────────────────────────────────────────────────────

def test_vision_detection_valid():
    det = VisionDetection(class_name="cotton_aphids", category="pest", confidence=0.91, count=3)
    assert det.class_name == "cotton_aphids"
    assert det.category == "pest"
    assert det.confidence == 0.91
    assert det.count == 3


def test_vision_detection_category_constraint():
    with pytest.raises(ValidationError):
        VisionDetection(class_name="cotton_aphids", category="neutral", confidence=0.9, count=1)


def test_vision_detection_confidence_bounds():
    with pytest.raises(ValidationError):
        VisionDetection(class_name="cotton_aphids", category="pest", confidence=1.5, count=1)
    with pytest.raises(ValidationError):
        VisionDetection(class_name="cotton_aphids", category="pest", confidence=-0.1, count=1)


def test_vision_detection_count_non_negative():
    with pytest.raises(ValidationError):
        VisionDetection(class_name="cotton_aphids", category="pest", confidence=0.8, count=-1)


def test_vision_result_schema_serialization():
    det = VisionDetection(**{"class": "cotton_aphids", "category": "pest", "confidence": 0.91, "count": 1})
    res = VisionResult(station_id=3, view="upper", detections=[det])

    dumped = res.model_dump(by_alias=True)
    assert dumped["station_id"] == 3
    assert dumped["view"] == "upper"
    assert len(dumped["detections"]) == 1
    assert dumped["detections"][0]["class"] == "cotton_aphids"
    assert dumped["detections"][0]["category"] == "pest"
    assert dumped["detections"][0]["confidence"] == 0.91
    assert dumped["detections"][0]["count"] == 1

    # Backward compatibility properties
    assert len(res.pests) == 1
    assert res.pests[0].name == "cotton_aphids"
    assert len(res.defenders) == 0
    assert res.overall_confidence == 0.91


# ─────────────────────────────────────────────────────────────
# 3. Image Preprocessing Tests
# ─────────────────────────────────────────────────────────────

def _make_dummy_jpeg() -> bytes:
    from PIL import Image
    bio = io.BytesIO()
    img = Image.new("RGB", (64, 64), color=(0, 128, 0))
    img.save(bio, format="JPEG")
    return bio.getvalue()


def test_preprocessor_valid_jpeg():
    raw_jpeg = _make_dummy_jpeg()
    img, meta = ImagePreprocessor.preprocess(raw_jpeg)
    assert meta.width == 64
    assert meta.height == 64
    assert meta.format == "JPEG"
    assert meta.mode == "RGB"
    assert meta.size_bytes > 0


def test_preprocessor_empty_bytes():
    with pytest.raises(InvalidImageError, match="empty or null"):
        ImagePreprocessor.preprocess(b"")


def test_preprocessor_corrupted_bytes():
    with pytest.raises(InvalidImageError):
        ImagePreprocessor.preprocess(b"\xff\xd8\xff\xe0" + b"\x00" * 30 + b"corrupted garbage")


# ─────────────────────────────────────────────────────────────
# 4. MockVisionProvider Tests
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mock_provider_station_profiles():
    provider = MockVisionProvider()
    valid_jpeg = _make_dummy_jpeg()

    # Station 1: Defenders present
    res1 = await provider.analyze_image(valid_jpeg, station_id=1, view="lower")
    assert res1.status == VisionStatus.SUCCESS
    assert any(d.category == "defender" for d in res1.detections)

    # Station 5: High pests
    res5 = await provider.analyze_image(valid_jpeg, station_id=5, view="middle")
    assert res5.status == VisionStatus.SUCCESS
    assert any(d.category == "pest" for d in res5.detections)

    # Station 10: Clean canopy
    res10 = await provider.analyze_image(valid_jpeg, station_id=10, view="upper")
    assert res10.status == VisionStatus.NO_DETECTIONS
    assert len(res10.detections) == 0


@pytest.mark.asyncio
async def test_mock_provider_scenarios_a_through_g():
    provider = MockVisionProvider()

    # A. Empty
    sa = provider.get_scenario_a_empty()
    assert sa.status == VisionStatus.NO_DETECTIONS
    assert len(sa.detections) == 0

    # B. Multiple pests
    sb = provider.get_scenario_b_multiple_pests()
    assert sb.status == VisionStatus.SUCCESS
    assert all(d.category == "pest" for d in sb.detections)
    assert len(sb.detections) >= 2

    # C. Multiple defenders
    sc = provider.get_scenario_c_multiple_defenders()
    assert sc.status == VisionStatus.SUCCESS
    assert all(d.category == "defender" for d in sc.detections)

    # D. Mixed
    sd = provider.get_scenario_d_mixed()
    assert any(d.category == "pest" for d in sd.detections)
    assert any(d.category == "defender" for d in sd.detections)

    # E. Views
    se = provider.get_scenario_e_canopy_views()
    assert "lower" in se and "middle" in se and "upper" in se
    assert se["lower"].view == CanopyView.LOWER
    assert se["upper"].view == CanopyView.UPPER

    # F. Image unavailable
    sf = provider.get_scenario_f_image_unavailable()
    assert sf.status == VisionStatus.IMAGE_UNAVAILABLE
    assert len(sf.detections) == 0

    # G. Low confidence
    sg = provider.get_scenario_g_low_confidence()
    assert sg.status == VisionStatus.SUCCESS
    assert sg.detections[0].confidence < 0.35


# ─────────────────────────────────────────────────────────────
# 5. YOLOVisionProvider Tests
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_yolo_provider_unconfigured_model():
    provider = YOLOVisionProvider(model_path="")
    assert not provider.is_configured()

    valid_jpeg = _make_dummy_jpeg()
    res = await provider.analyze_image(valid_jpeg, station_id=3, view="middle")
    assert res.status == VisionStatus.MODEL_NOT_CONFIGURED
    assert "not configured" in res.error_message.lower()
    assert len(res.detections) == 0


@pytest.mark.asyncio
async def test_yolo_provider_missing_file():
    provider = YOLOVisionProvider(model_path="non_existent_weights.pt")
    assert not provider.is_configured()

    valid_jpeg = _make_dummy_jpeg()
    res = await provider.analyze_image(valid_jpeg, station_id=1)
    assert res.status == VisionStatus.MODEL_NOT_CONFIGURED
    assert "not found" in res.error_message.lower()


@pytest.mark.asyncio
async def test_yolo_provider_invalid_image():
    provider = YOLOVisionProvider(model_path="")
    res = await provider.analyze_image(b"not an image", station_id=1)
    assert res.status == VisionStatus.IMAGE_INVALID


# ─────────────────────────────────────────────────────────────
# 6. VisionService Tests
# ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vision_service_mode_dispatching():
    service = VisionService()
    valid_jpeg = _make_dummy_jpeg()

    # In DEMO mode (default)
    service.set_mode("DEMO")
    res_demo = await service.analyze_frame(valid_jpeg, station_id=2, view="middle")
    assert res_demo.provider in ("mock", "mockvisionprovider")
    assert res_demo.status == VisionStatus.SUCCESS

    # In LIVE mode (without model path configured)
    service.set_mode("LIVE")
    res_live = await service.analyze_frame(valid_jpeg, station_id=2, view="middle")
    assert res_live.status == VisionStatus.MODEL_NOT_CONFIGURED


@pytest.mark.asyncio
async def test_vision_service_empty_image():
    service = VisionService()
    res = await service.analyze_frame(b"")
    assert res.status == VisionStatus.IMAGE_UNAVAILABLE


# ─────────────────────────────────────────────────────────────
# 7. Integration Safety Boundary Tests
# ─────────────────────────────────────────────────────────────

def test_vision_does_not_depend_on_motion_or_hardware():
    import backend.services.vision.service as vs
    import backend.services.vision.yolo_provider as yp
    import backend.services.vision.mock_provider as mp

    # Ensure vision modules do not import hardware or motion controllers
    for mod in (vs, yp, mp):
        mod_src = mod.__file__
        with open(mod_src, "r", encoding="utf-8") as f:
            content = f.read()
            assert "cmd_vel" not in content
            assert "motor" not in content.lower()
            assert "gpio" not in content.lower()


# ─────────────────────────────────────────────────────────────
# 8. API Endpoint Tests
# ─────────────────────────────────────────────────────────────

def test_api_vision_classes():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.get("/api/vision/classes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["pests"]) == 6
    assert len(data["defenders"]) == 5
    assert data["total_classes"] == 11


def test_api_vision_status():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.get("/api/vision/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_provider" in data
    assert "model_configured" in data


def test_api_vision_analyze_valid_base64():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    raw_jpeg = _make_dummy_jpeg()
    b64_str = base64.b64encode(raw_jpeg).decode("utf-8")

    resp = client.post(
        "/api/vision/analyze",
        json={"image_base64": b64_str, "station_id": 2, "view": "middle"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["station_id"] == 2
    assert data["view"] == "middle"
    assert "detections" in data
    assert data["status"] in ("success", "no_detections")


def test_api_vision_analyze_corrupted_base64():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/vision/analyze",
        json={"image_base64": "not-valid-base64!!", "station_id": 1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "image_invalid"
    assert len(data["detections"]) == 0
