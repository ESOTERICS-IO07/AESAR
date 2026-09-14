from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from backend.config.settings import settings
from backend.models.schemas import CanopyView, VisionDetection, VisionResult, VisionStatus
from backend.services.vision.base import BaseVisionProvider
from backend.services.vision.classes import (
    ALL_CANONICAL_CLASSES,
    get_class_category,
    is_valid_vision_class,
    resolve_class_name,
)

logger = logging.getLogger("aesar.vision.remote")


class RemoteVisionProvider(BaseVisionProvider):
    """
    Adapts the standalone AESAR-Vision FastAPI service (Machine 2) to the
    canonical VisionResult contract in ARACHNID-main (Machine 1).

    Adheres strictly to the AESAR Master Implementation Contract v2.1:
    - Never fabricates detections in LIVE mode
    - Returns honest error/unavailable state on network failure, timeout, or stale observations
    - Maps remote detections strictly to canonical 11 AESAR classes
    - Machine 1 receives structured JSON only; zero image bytes transferred over network
    - Preserves exact VisionResult schema
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: float = 4.0,
        max_staleness_seconds: float = 5.0,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = (base_url or getattr(settings, "aesar_vision_url", "http://localhost:8001")).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_staleness_seconds = max_staleness_seconds
        self._client = client

    async def check_health(self) -> bool:
        """Ping remote AESAR-Vision camera status endpoint."""
        url = f"{self.base_url}/api/status"
        try:
            if self._client:
                resp = await self._client.get(url)
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return bool(data.get("connected", False))
            return False
        except Exception as e:
            logger.debug(f"Remote vision health check failed ({url}): {e}")
            return False

    async def analyze_image(
        self,
        image_bytes: bytes,
        station_id: Optional[int] = None,
        view: Optional[str] = None,
    ) -> VisionResult:
        """
        Fetches the active AI observation from the remote AESAR-Vision service.
        Adapts the remote JSON payload into a canonical VisionResult.
        """
        norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None
        status_url = f"{self.base_url}/api/ai/status"

        # 1. Fetch AI status from remote AESAR-Vision
        try:
            if self._client:
                resp = await self._client.get(status_url)
            else:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    resp = await client.get(status_url)
        except (httpx.RequestError, httpx.TimeoutException, ConnectionError, OSError) as e:
            logger.warning(f"Remote vision service unreachable at {status_url}: {e}")
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_UNAVAILABLE,
                error_message=f"Remote vision service unreachable at {self.base_url}: {e}",
                provider="remote",
            )
        except Exception as e:
            logger.error(f"Unexpected error querying remote vision service: {e}")
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=f"Remote query failure: {e}",
                provider="remote",
            )

        # 2. Check HTTP status
        if resp.status_code != 200:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=f"Remote vision service returned HTTP {resp.status_code}",
                provider="remote",
            )

        # 3. Parse and adapt remote payload
        try:
            data = resp.json()
        except Exception as e:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=f"Failed to parse remote JSON response: {e}",
                provider="remote",
            )

        remote_state = data.get("state", "unknown")

        if remote_state == "model_loading":
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.MODEL_NOT_CONFIGURED,
                error_message=data.get("detail") or "Remote model is loading",
                provider="remote",
            )

        if remote_state == "model_unavailable":
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.MODEL_NOT_CONFIGURED,
                error_message=data.get("detail") or "Remote YOLO model unavailable",
                provider="remote",
            )

        if remote_state == "inference_error":
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=data.get("detail") or "Remote inference error",
                provider="remote",
            )

        if remote_state != "ai_ready":
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=f"Remote AI state is not ready: {remote_state}",
                provider="remote",
            )

        # 4. Freshness check on updated_at
        updated_at = data.get("updated_at")
        if updated_at is not None:
            try:
                age = time.time() - float(updated_at)
                if age > self.max_staleness_seconds:
                    logger.warning(
                        f"Remote observation is stale (age={age:.2f}s > max={self.max_staleness_seconds}s)"
                    )
                    return VisionResult(
                        station_id=station_id,
                        view=norm_view,
                        detections=[],
                        status=VisionStatus.IMAGE_UNAVAILABLE,
                        error_message=f"Remote vision observation is stale (age: {age:.1f}s, max allowed: {self.max_staleness_seconds}s)",
                        provider="remote",
                        image_metadata={
                            "evidence_url": f"{self.base_url}/api/ai/annotated",
                            "stream_url": f"{self.base_url}/api/stream",
                            "stale": True,
                            "observation_age_seconds": round(age, 2),
                        },
                    )
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse updated_at timestamp '{updated_at}': {e}")

        # 5. Extract and filter canonical detections
        raw_detections = data.get("detections", [])
        valid_detections: List[VisionDetection] = []

        for d in raw_detections:
            raw_name = d.get("class_name")
            if not raw_name:
                continue

            canonical_class = resolve_class_name(raw_name)
            if not is_valid_vision_class(canonical_class):
                # Filter out unsupported / non-canonical classes
                continue

            category = d.get("category") or get_class_category(canonical_class)
            confidence = round(float(d.get("confidence", 0.0)), 3)
            count = int(d.get("count", 1))

            valid_detections.append(
                VisionDetection(
                    class_name=canonical_class,
                    category=category,
                    confidence=confidence,
                    count=count,
                )
            )

        status = VisionStatus.SUCCESS if valid_detections else VisionStatus.NO_DETECTIONS

        # 6. Structured metadata with evidence link (NO binary image transfer)
        image_meta = {
            "evidence_url": f"{self.base_url}/api/ai/annotated",
            "stream_url": f"{self.base_url}/api/stream",
            "remote_fps": data.get("inference_fps"),
            "updated_at": updated_at,
        }

        return VisionResult(
            station_id=station_id,
            view=norm_view,
            detections=valid_detections,
            status=status,
            model_name="aesar-pest-yolo11s (remote)",
            provider="remote",
            image_metadata=image_meta,
        )
