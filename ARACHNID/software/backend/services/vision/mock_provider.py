from __future__ import annotations

import logging
from typing import Dict, List, Optional

from backend.models.schemas import (
    CanopyView,
    ImageQuality,
    PlantHealth,
    VisionDetection,
    VisionResult,
    VisionStatus,
)
from backend.services.vision.base import BaseVisionProvider
from backend.services.vision.classes import (
    DEFENDER_CARABID_BEETLE,
    DEFENDER_GREEN_LACEWING,
    DEFENDER_LADYBIRD_BEETLE,
    DEFENDER_LYCOSA_WOLF_SPIDER,
    DEFENDER_MIRID_BUG,
    PEST_AMERICAN_BOLLWORM,
    PEST_BROWN_PLANTHOPPER,
    PEST_CHILLI_THRIPS,
    PEST_COTTON_APHIDS,
    PEST_GREEN_LEAFHOPPER,
    PEST_YELLOW_STEM_BORER,
)
from backend.services.vision.preprocessor import ImagePreprocessor, InvalidImageError

logger = logging.getLogger("aesar.vision.mock")


class MockVisionProvider(BaseVisionProvider):
    """
    Contract-compliant deterministic mock vision provider for DEMO mode and automated testing.
    Uses the 11 authoritative AESAR contract classes (6 pests, 5 defenders).
    Requires no GPU, no weights, and no external network calls.
    """

    # Authoritative station scenarios mapped to stations 1..10
    STATION_SCENARIOS: Dict[int, List[VisionDetection]] = {
        # Station 1: Pristine - Defenders present (Ladybird Beetles)
        1: [
            VisionDetection(class_name=DEFENDER_LADYBIRD_BEETLE, category="defender", confidence=0.92, count=3),
        ],
        # Station 2: Balanced - Low pests with active wolf spider & ladybird
        2: [
            VisionDetection(class_name=PEST_COTTON_APHIDS, category="pest", confidence=0.88, count=2),
            VisionDetection(class_name=DEFENDER_LADYBIRD_BEETLE, category="defender", confidence=0.91, count=2),
            VisionDetection(class_name=DEFENDER_LYCOSA_WOLF_SPIDER, category="defender", confidence=0.86, count=1),
        ],
        # Station 3: Emerging outbreak - Brown planthoppers rising
        3: [
            VisionDetection(class_name=PEST_BROWN_PLANTHOPPER, category="pest", confidence=0.89, count=14),
            VisionDetection(class_name=DEFENDER_MIRID_BUG, category="defender", confidence=0.82, count=1),
        ],
        # Station 4: Balanced - Chilli thrips suppressed by green lacewings
        4: [
            VisionDetection(class_name=PEST_CHILLI_THRIPS, category="pest", confidence=0.85, count=4),
            VisionDetection(class_name=DEFENDER_GREEN_LACEWING, category="defender", confidence=0.90, count=2),
        ],
        # Station 5: Severe outbreak - High cotton aphids, no defenders
        5: [
            VisionDetection(class_name=PEST_COTTON_APHIDS, category="pest", confidence=0.94, count=22),
            VisionDetection(class_name=PEST_CHILLI_THRIPS, category="pest", confidence=0.87, count=8),
        ],
        # Station 6: Moderate - Green leafhopper present, carabid beetle hunting
        6: [
            VisionDetection(class_name=PEST_GREEN_LEAFHOPPER, category="pest", confidence=0.84, count=6),
            VisionDetection(class_name=DEFENDER_CARABID_BEETLE, category="defender", confidence=0.89, count=1),
        ],
        # Station 7: Critical pest infestation - Yellow stem borer & bollworm
        7: [
            VisionDetection(class_name=PEST_YELLOW_STEM_BORER, category="pest", confidence=0.91, count=5),
            VisionDetection(class_name=PEST_AMERICAN_BOLLWORM, category="pest", confidence=0.89, count=3),
        ],
        # Station 8: High thrips & planthoppers
        8: [
            VisionDetection(class_name=PEST_CHILLI_THRIPS, category="pest", confidence=0.88, count=16),
            VisionDetection(class_name=PEST_BROWN_PLANTHOPPER, category="pest", confidence=0.85, count=7),
            VisionDetection(class_name=DEFENDER_LYCOSA_WOLF_SPIDER, category="defender", confidence=0.79, count=1),
        ],
        # Station 9: Well-defended equilibrium - Ladybirds and lacewings
        9: [
            VisionDetection(class_name=DEFENDER_LADYBIRD_BEETLE, category="defender", confidence=0.93, count=4),
            VisionDetection(class_name=DEFENDER_GREEN_LACEWING, category="defender", confidence=0.87, count=2),
        ],
        # Station 10: Pristine canopy - 0 detections
        10: [],
    }

    async def analyze_image(
        self,
        image_bytes: bytes,
        station_id: Optional[int] = None,
        view: Optional[str] = None,
    ) -> VisionResult:
        """
        Returns contract-compliant VisionResult for the given station and view.
        Validates image buffer format; handles invalid buffers safely.
        """
        norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None

        # Validate image buffer
        if not image_bytes:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_UNAVAILABLE,
                error_message="Image buffer is empty or unavailable.",
                provider="mock",
            )

        # Catch corrupted / completely invalid image buffers
        if len(image_bytes) < 4 or not ImagePreprocessor.validate_magic_bytes(image_bytes):
            # Allow mock tests with short test signatures if needed, otherwise validate
            if not image_bytes.startswith(b"\xff\xd8") and not image_bytes.startswith(b"\x89PNG"):
                return VisionResult(
                    station_id=station_id,
                    view=norm_view,
                    detections=[],
                    status=VisionStatus.IMAGE_INVALID,
                    error_message="Invalid image format; expected JPEG or PNG.",
                    provider="mock",
                )

        st_num = station_id if station_id is not None else 1
        # Lookup station scenario or default based on modulo
        scenario_idx = ((st_num - 1) % 10) + 1
        detections = [
            VisionDetection(
                class_name=d.class_name,
                category=d.category,
                confidence=d.confidence,
                count=d.count,
            )
            for d in self.STATION_SCENARIOS.get(scenario_idx, [])
        ]

        # View-specific adjustments (e.g., lower view often has more soil-dwelling carabid / spiders)
        if norm_view == CanopyView.LOWER and not detections:
            detections = [
                VisionDetection(class_name=DEFENDER_CARABID_BEETLE, category="defender", confidence=0.88, count=1)
            ]
        elif norm_view == CanopyView.UPPER and scenario_idx == 10:
            detections = []

        status = VisionStatus.SUCCESS if detections else VisionStatus.NO_DETECTIONS
        health = (
            PlantHealth.SEVERE_STRESS
            if scenario_idx in (5, 7)
            else PlantHealth.MODERATE_STRESS
            if scenario_idx in (3, 6, 8)
            else PlantHealth.HEALTHY
        )

        return VisionResult(
            station_id=station_id,
            view=norm_view,
            detections=detections,
            status=status,
            plant_health=health,
            image_quality=ImageQuality.GOOD,
            provider="mock",
        )

    # Helper methods for contract mock scenarios A through G
    def get_scenario_a_empty(self, station_id: int = 10, view: str = "middle") -> VisionResult:
        """Scenario A: Empty detections (clean foliage, 0 pests, 0 defenders)."""
        return VisionResult(
            station_id=station_id,
            view=CanopyView(view),
            detections=[],
            status=VisionStatus.NO_DETECTIONS,
            plant_health=PlantHealth.HEALTHY,
            image_quality=ImageQuality.EXCELLENT,
            provider="mock",
        )

    def get_scenario_b_multiple_pests(self, station_id: int = 5, view: str = "middle") -> VisionResult:
        """Scenario B: Multiple pest detections."""
        return VisionResult(
            station_id=station_id,
            view=CanopyView(view),
            detections=[
                VisionDetection(class_name=PEST_COTTON_APHIDS, category="pest", confidence=0.92, count=18),
                VisionDetection(class_name=PEST_CHILLI_THRIPS, category="pest", confidence=0.86, count=6),
            ],
            status=VisionStatus.SUCCESS,
            plant_health=PlantHealth.SEVERE_STRESS,
            image_quality=ImageQuality.GOOD,
            provider="mock",
        )

    def get_scenario_c_multiple_defenders(self, station_id: int = 1, view: str = "lower") -> VisionResult:
        """Scenario C: Multiple defender detections."""
        return VisionResult(
            station_id=station_id,
            view=CanopyView(view),
            detections=[
                VisionDetection(class_name=DEFENDER_LADYBIRD_BEETLE, category="defender", confidence=0.94, count=4),
                VisionDetection(class_name=DEFENDER_LYCOSA_WOLF_SPIDER, category="defender", confidence=0.89, count=2),
                VisionDetection(class_name=DEFENDER_GREEN_LACEWING, category="defender", confidence=0.91, count=1),
            ],
            status=VisionStatus.SUCCESS,
            plant_health=PlantHealth.HEALTHY,
            image_quality=ImageQuality.EXCELLENT,
            provider="mock",
        )

    def get_scenario_d_mixed(self, station_id: int = 2, view: str = "middle") -> VisionResult:
        """Scenario D: Mixed pests and beneficial defenders."""
        return VisionResult(
            station_id=station_id,
            view=CanopyView(view),
            detections=[
                VisionDetection(class_name=PEST_BROWN_PLANTHOPPER, category="pest", confidence=0.88, count=5),
                VisionDetection(class_name=DEFENDER_MIRID_BUG, category="defender", confidence=0.85, count=3),
                VisionDetection(class_name=DEFENDER_CARABID_BEETLE, category="defender", confidence=0.90, count=1),
            ],
            status=VisionStatus.SUCCESS,
            plant_health=PlantHealth.MODERATE_STRESS,
            image_quality=ImageQuality.GOOD,
            provider="mock",
        )

    def get_scenario_e_canopy_views(self, station_id: int = 3) -> Dict[str, VisionResult]:
        """Scenario E: Different canopy views (lower, middle, upper)."""
        return {
            "lower": VisionResult(
                station_id=station_id,
                view=CanopyView.LOWER,
                detections=[
                    VisionDetection(class_name=DEFENDER_CARABID_BEETLE, category="defender", confidence=0.91, count=2)
                ],
                status=VisionStatus.SUCCESS,
                provider="mock",
            ),
            "middle": VisionResult(
                station_id=station_id,
                view=CanopyView.MIDDLE,
                detections=[
                    VisionDetection(class_name=PEST_BROWN_PLANTHOPPER, category="pest", confidence=0.87, count=8)
                ],
                status=VisionStatus.SUCCESS,
                provider="mock",
            ),
            "upper": VisionResult(
                station_id=station_id,
                view=CanopyView.UPPER,
                detections=[
                    VisionDetection(class_name=PEST_COTTON_APHIDS, category="pest", confidence=0.90, count=4)
                ],
                status=VisionStatus.SUCCESS,
                provider="mock",
            ),
        }

    def get_scenario_f_image_unavailable(self, station_id: int = 4, view: str = "upper") -> VisionResult:
        """Scenario F: Image unavailable."""
        return VisionResult(
            station_id=station_id,
            view=CanopyView(view),
            detections=[],
            status=VisionStatus.IMAGE_UNAVAILABLE,
            error_message="Camera frame capture timed out; optics unavailable.",
            provider="mock",
        )

    def get_scenario_g_low_confidence(self, station_id: int = 8, view: str = "upper") -> VisionResult:
        """Scenario G: Low-confidence detection."""
        return VisionResult(
            station_id=station_id,
            view=CanopyView(view),
            detections=[
                VisionDetection(class_name=PEST_AMERICAN_BOLLWORM, category="pest", confidence=0.28, count=1)
            ],
            status=VisionStatus.SUCCESS,
            image_quality=ImageQuality.POOR,
            provider="mock",
        )
