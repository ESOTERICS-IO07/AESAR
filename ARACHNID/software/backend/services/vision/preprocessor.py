from __future__ import annotations

import io
import logging
from typing import Optional, Tuple
from PIL import Image, ImageOps
from pydantic import BaseModel

logger = logging.getLogger("aesar.vision.preprocessor")


class InvalidImageError(ValueError):
    """Raised when provided image bytes are invalid, empty, or corrupted."""
    pass


class ImageMetadata(BaseModel):
    width: int
    height: int
    format: str
    mode: str
    size_bytes: int
    aspect_ratio: float


class ImagePreprocessor:
    """
    Image Preprocessing layer for AESAR Vision AI.
    Validates, decodes, and standardizes image buffers before passing to YOLO/Mock inference.
    Preserves original image fidelity and never crops or destroys raw data arbitrarily.
    """

    # Magic byte signatures
    MAGIC_JPEG = b"\xff\xd8"
    MAGIC_PNG = b"\x89PNG\r\n\x1a\n"
    MAGIC_WEBP = b"RIFF"

    @classmethod
    def validate_magic_bytes(cls, image_bytes: bytes) -> bool:
        if len(image_bytes) < 4:
            return False
        return (
            image_bytes.startswith(cls.MAGIC_JPEG)
            or image_bytes.startswith(cls.MAGIC_PNG[:4])
            or (image_bytes.startswith(cls.MAGIC_WEBP) and b"WEBP" in image_bytes[:16])
        )

    @classmethod
    def preprocess(
        cls,
        image_bytes: bytes,
        target_size: Optional[Tuple[int, int]] = None,
    ) -> Tuple[Image.Image, ImageMetadata]:
        """
        Validates, decodes and checks image integrity.
        Returns the decoded PIL Image in RGB mode along with structured ImageMetadata.
        Raises InvalidImageError on empty, truncated, or unreadable input.
        """
        if not image_bytes:
            raise InvalidImageError("Image byte buffer is empty or null")

        if len(image_bytes) < 16:
            raise InvalidImageError(f"Image buffer too small ({len(image_bytes)} bytes); not a valid image")

        try:
            bio = io.BytesIO(image_bytes)
            img = Image.open(bio)
            
            # Verify internal structure without full load first
            img_format = img.format or "UNKNOWN"
            
            # Now load image data to catch truncation or broken JPEG blocks
            img.load()
            
            # Handle EXIF rotation if present
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            width, height = img.size
            if width <= 0 or height <= 0:
                raise InvalidImageError(f"Invalid image dimensions ({width}x{height})")

            # Standardize color representation to RGB
            if img.mode != "RGB":
                img = img.convert("RGB")

            metadata = ImageMetadata(
                width=width,
                height=height,
                format=img_format,
                mode=img.mode,
                size_bytes=len(image_bytes),
                aspect_ratio=round(width / max(1, height), 2),
            )

            # Optional model-specific resizing only if explicitly requested
            if target_size and (width, height) != target_size:
                img = img.resize(target_size, Image.Resampling.BILINEAR)

            return img, metadata

        except (IOError, SyntaxError, ValueError) as e:
            logger.warning(f"Image preprocessing failed: {e}")
            raise InvalidImageError(f"Failed to decode image: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected image preprocessing error: {e}")
            raise InvalidImageError(f"Corrupted or unsupported image buffer: {e}") from e
