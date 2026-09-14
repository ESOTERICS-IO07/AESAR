from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from backend.models.schemas import VisionResult


class BaseVisionProvider(ABC):
    """Abstract interface for agricultural vision observation providers."""

    @abstractmethod
    async def analyze_image(
        self,
        image_bytes: bytes,
        station_id: Optional[int] = None,
        view: Optional[str] = None,
    ) -> VisionResult:
        """
        Analyze the given plant leaf/crop image bytes and return structured observation.
        """
        pass
