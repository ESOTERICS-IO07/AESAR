from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config.settings import settings
from backend.models.schemas import CanopyView, VisionDetection, VisionResult, VisionStatus
from backend.services.vision.base import BaseVisionProvider
from backend.services.vision.classes import (
    ALL_CANONICAL_CLASSES,
    get_class_category,
    resolve_class_name,
)
from backend.services.vision.preprocessor import ImagePreprocessor, InvalidImageError

logger = logging.getLogger("aesar.vision.yolo")


class YOLOVisionProvider(BaseVisionProvider):
    """
    YOLO Object Detection Provider for AESAR.
    Detects and aggregates the 11 authoritative contract classes (6 pests, 5 defenders).
    
    If model weights are missing or unconfigured, reports honest MODEL_NOT_CONFIGURED status.
    Never fabricates detections, never downloads arbitrary models, and never claims unproven accuracy.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        device: Optional[str] = None,
    ) -> None:
        self.model_path = model_path if model_path is not None else settings.vision_model_path
        self.confidence_threshold = (
            confidence_threshold if confidence_threshold is not None else settings.vision_confidence_threshold
        )
        self.device = device if device is not None else settings.vision_device

        self._model: Any = None
        self._model_loaded: bool = False
        self._init_error: Optional[str] = None

        self._attempt_load_model()

    def _attempt_load_model(self) -> None:
        """Attempt to load YOLO model weights if configured on disk."""
        if not self.model_path:
            self._model_loaded = False
            self._init_error = "VISION_MODEL_PATH is not configured."
            logger.info("YOLO model not configured: VISION_MODEL_PATH is empty.")
            return

        resolved_path = Path(self.model_path)
        if not resolved_path.exists():
            self._model_loaded = False
            self._init_error = f"Model weights not found on disk at '{self.model_path}'."
            logger.warning(f"YOLO model weights missing: '{self.model_path}' does not exist.")
            return

        try:
            from ultralytics import YOLO  # type: ignore

            logger.info(f"Loading YOLO model weights from '{self.model_path}' on device '{self.device}'...")
            self._model = YOLO(str(resolved_path))
            self._model_loaded = True
            self._init_error = None
            logger.info("YOLO model loaded successfully!")
        except ImportError:
            self._model_loaded = False
            self._init_error = "Inference library 'ultralytics' is not installed in the environment."
            logger.warning(self._init_error)
        except Exception as e:
            self._model_loaded = False
            self._init_error = f"Failed to initialize YOLO model: {e}"
            logger.error(self._init_error)

    def is_configured(self) -> bool:
        """True only if valid model weights exist and are successfully loaded."""
        return self._model_loaded and self._model is not None

    async def analyze_image(
        self,
        image_bytes: bytes,
        station_id: Optional[int] = None,
        view: Optional[str] = None,
    ) -> VisionResult:
        """
        Runs YOLO object detection on the preprocessed image.
        Aggregates multiple bounding boxes per class into counts and average confidence.
        """
        norm_view = CanopyView(view.lower()) if view and view.lower() in ("lower", "middle", "upper") else None

        # 1. Preprocess & Validate Image
        try:
            pil_img, meta = ImagePreprocessor.preprocess(image_bytes)
        except InvalidImageError as e:
            logger.warning(f"YOLO rejected invalid image: {e}")
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_INVALID,
                error_message=str(e),
                provider="yolo",
            )
        except Exception as e:
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.IMAGE_UNAVAILABLE,
                error_message=f"Image unavailable: {e}",
                provider="yolo",
            )

        # 2. Verify Model State
        if not self.is_configured():
            logger.info(f"YOLO inference skipped: {self._init_error}")
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.MODEL_NOT_CONFIGURED,
                error_message=self._init_error or "Model weights not configured.",
                model_name=self.model_path or "unconfigured",
                image_metadata=meta.model_dump(),
                provider="yolo",
            )

        # 3. Run Inference
        try:
            results = self._model(pil_img, conf=self.confidence_threshold, device=self.device, verbose=False)
            boxes = results[0].boxes if results else None
        except Exception as e:
            logger.error(f"YOLO inference failed: {e}")
            return VisionResult(
                station_id=station_id,
                view=norm_view,
                detections=[],
                status=VisionStatus.INFERENCE_FAILURE,
                error_message=f"Inference execution error: {e}",
                model_name=self.model_path,
                image_metadata=meta.model_dump(),
                provider="yolo",
            )

        # 4. Extract & Aggregate Detections
        # Raw box storage by resolved canonical class name: class -> list of confidences
        raw_detections: Dict[str, List[float]] = {}

        if boxes is not None and len(boxes) > 0:
            names_dict = results[0].names or {}
            for box in boxes:
                cls_id = int(box.cls[0].item()) if hasattr(box.cls, "__len__") else int(box.cls.item())
                conf = float(box.conf[0].item()) if hasattr(box.conf, "__len__") else float(box.conf.item())

                raw_label = names_dict.get(cls_id, str(cls_id))
                canonical_class = resolve_class_name(raw_label)

                if canonical_class not in raw_detections:
                    raw_detections[canonical_class] = []
                raw_detections[canonical_class].append(conf)

        aggregated_detections: List[VisionDetection] = []
        for c_class, conf_list in raw_detections.items():
            count = len(conf_list)
            avg_conf = round(sum(conf_list) / count, 3)
            category = get_class_category(c_class)

            aggregated_detections.append(
                VisionDetection(
                    class_name=c_class,
                    category=category,
                    confidence=avg_conf,
                    count=count,
                )
            )

        status = VisionStatus.SUCCESS if aggregated_detections else VisionStatus.NO_DETECTIONS

        return VisionResult(
            station_id=station_id,
            view=norm_view,
            detections=aggregated_detections,
            status=status,
            model_name=self.model_path,
            image_metadata=meta.model_dump(),
            provider="yolo",
        )
