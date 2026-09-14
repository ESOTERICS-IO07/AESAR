from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from google import genai
from google.genai import types

from backend.config.settings import settings
from backend.models.schemas import (
    ImageQuality,
    PlantHealth,
    VisionAnalysisResult,
)
from backend.services.vision.base import BaseVisionProvider

logger = logging.getLogger("aesar.vision.gemini")

SYSTEM_PROMPT = """You are an agricultural visual observation assistant.
Analyze ONLY what is visibly present in the provided plant image.

Your task is to identify visible members of these MVP categories:

PESTS:
- aphids (aphid)
- thrips (thrips)

BENEFICIAL DEFENDERS:
- ladybirds/ladybugs (ladybird)
- spiders (spider)

For each category:
- estimate visible count
- provide confidence (0.0 to 1.0)
- DO NOT invent objects or pests that are not clearly visible.
- if the image is blurry or distant, return low confidence (< 0.5) and set image_quality accordingly.
- if an insect cannot be confidently identified, classify it as unknown or omit rather than guessing.

Also assess visible plant condition:
- healthy
- mild_stress
- moderate_stress
- severe_stress
- unknown

Identify visible symptoms such as:
- holes
- discoloration
- curling
- wilting
- visible_insect_damage

CRITICAL CONSTRAINTS:
This is an observation system, NOT a pesticide prescription system.
Do not recommend chemical application from the image alone.
Return only the structured JSON complying with the requested schema.
"""


class GeminiVisionProvider(BaseVisionProvider):
    """
    Live Vision Observation Provider utilizing Google GenAI SDK (Gemini).
    Uses strict schema enforcement, low temperature, and zero-hallucination prompts.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.timeout_seconds = timeout_seconds

        if not self.api_key:
            logger.warning("GeminiVisionProvider initialized without GEMINI_API_KEY. Calls will fail or fallback.")
            self._client = None
        else:
            self._client = genai.Client(api_key=self.api_key)

    async def analyze_image(
        self,
        image_bytes: bytes,
        station_id: Optional[int] = None,
    ) -> VisionAnalysisResult:
        if not self._client:
            raise ValueError("Gemini API key is not configured")

        if not image_bytes:
            raise ValueError("Image bytes cannot be empty")

        def _call_gemini() -> VisionAnalysisResult:
            prompt_contents = [
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                types.Part.from_text(text=SYSTEM_PROMPT),
            ]

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VisionAnalysisResult,
                temperature=0.1,
            )

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt_contents,
                config=config,
            )

            if not response.text:
                raise RuntimeError("Empty response received from Gemini model")

            return VisionAnalysisResult.model_validate_json(response.text)

        # Run synchronous SDK call in threadpool with timeout protection
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(_call_gemini),
                timeout=self.timeout_seconds,
            )
            return result
        except asyncio.TimeoutError:
            logger.error(f"Gemini API request timed out after {self.timeout_seconds}s")
            raise TimeoutError(f"Gemini vision analysis timed out after {self.timeout_seconds}s")
        except Exception as e:
            logger.error(f"Gemini vision analysis error: {e}")
            raise
