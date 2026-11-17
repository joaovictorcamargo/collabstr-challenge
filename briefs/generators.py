"""Brief generators: Claude for real output, a templated demo generator for keyless runs."""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import anthropic
from django.conf import settings
from pydantic import ValidationError

from .prompts import SYSTEM_PROMPT, build_user_prompt
from .schemas import Brief, BriefInputs, brief_json_schema

logger = logging.getLogger(__name__)

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class GenerationError(Exception):
    """Base error. `user_message` is safe to show to the brand."""

    user_message = "We couldn't generate your brief. Please try again."


class GenerationFailed(GenerationError):
    """The model answered, but not with something we can use (refusal, truncation, bad JSON)."""

    user_message = "We couldn't turn that into a usable brief. Try again, or tweak your inputs."


class GenerationUnavailable(GenerationError):
    """The model could not be reached (timeout, rate limit, outage, misconfiguration)."""

    user_message = "Our brief writer is busy right now. Please try again in a moment."


class BriefGenerator(Protocol):
    source: str

    def generate(self, inputs: BriefInputs) -> Brief: ...


class AnthropicBriefGenerator:
    source = "anthropic"

    def __init__(self, client: Any, model: str) -> None:
        self.client = client
        self.model = model

    def generate(self, inputs: BriefInputs) -> Brief:
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=8000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": build_user_prompt(inputs)}],
                output_config={
                    "effort": "low",
                    "format": {"type": "json_schema", "schema": brief_json_schema()},
                },
                # Re-run on Anthropic's recommended model if a safety classifier
                # declines a benign request, instead of showing the user an error.
                betas=[FALLBACK_BETA],
                fallbacks="default",
            )
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as exc:
            logger.warning("anthropic unreachable: %s", type(exc).__name__)
            raise GenerationUnavailable(str(exc)) from exc
        except anthropic.APIStatusError as exc:
            logger.warning("anthropic status %s: %s", exc.status_code, type(exc).__name__)
            if exc.status_code in {400, 404, 413, 422}:
                raise GenerationFailed(str(exc)) from exc
            raise GenerationUnavailable(str(exc)) from exc

        if response.stop_reason != "end_turn":
            logger.warning("anthropic stop_reason=%s", response.stop_reason)
            raise GenerationFailed(f"stop_reason={response.stop_reason}")

        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            return Brief.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("anthropic output failed validation: %s", type(exc).__name__)
            raise GenerationFailed("invalid output") from exc


class DemoBriefGenerator:
    """Deterministic, templated briefs so the app runs without an API key.

    Shown in the UI with a "Demo content" badge; never presented as AI output.
    """

    source = "demo"

    _DELIVERABLES = {
        "instagram": [
            "1 Instagram Reel (15-45s), posted as a collab post",
            "3 Story frames with a link sticker",
        ],
        "tiktok": ["1 TikTok video (15-60s) on the creator's account", "Raw footage for Spark Ads"],
        "ugc": [
            "3 raw vertical videos (15-30s), unbranded",
            "5 product photos",
            "12-month paid usage rights",
        ],
    }
    _SIGNAL = {
        "awareness": "views and profile visits",
        "conversions": "link clicks and [discount code] redemptions",
        "content_assets": "the number of ad-ready assets delivered",
    }
    _VOICE = {
        "professional": "clear, credible and polished",
        "friendly": "warm, relatable and conversational",
        "playful": "fun, surprising and a little cheeky",
    }

    def generate(self, inputs: BriefInputs) -> Brief:
        brand, platform = inputs.brand_name, inputs.platform_label
        product = inputs.product_note or f"{brand}'s product"
        voice = self._VOICE[inputs.tone]
        signal = self._SIGNAL[inputs.goal]
        return Brief.model_validate(
            {
                "campaign_title": f"{brand} x Creators: {inputs.goal_label} on {platform}",
                "summary": (
                    f"A {platform} campaign for {brand} focused on {inputs.goal_label.lower()}. "
                    f"Creators show {product} in real, everyday moments in a {voice} voice."
                ),
                "objective": f"{inputs.goal_label}: measure success by {signal}.",
                "key_message": f"{brand} fits naturally into your day.",
                "deliverables": self._DELIVERABLES[inputs.platform],
                "dos": [
                    "Hook viewers in the first 2 seconds",
                    f"Show {product} in use, not just on a shelf",
                    f"Keep the voice {voice}",
                ],
                "donts": [
                    "Make claims the brand hasn't approved",
                    "Show competitor products",
                ],
                "content_angles": [
                    {
                        "title": "Day in the life",
                        "hook": f"Here's where {brand} shows up in my day",
                        "description": (
                            f"Follow the creator's routine with {product} as the turning point."
                        ),
                    },
                    {
                        "title": "Honest first impressions",
                        "hook": f"Trying {brand} for the first time",
                        "description": "Unboxing and a candid first try, with one clear takeaway.",
                    },
                    {
                        "title": "Problem to solution",
                        "hook": "If this sounds like you, keep watching",
                        "description": f"Name a common frustration, then show how {brand} helps.",
                    },
                ],
                "creator_criteria": [
                    {
                        "criterion": "Niche fit",
                        "detail": f"Creators whose content already fits {brand}'s category.",
                    },
                    {
                        "criterion": "Audience",
                        "detail": "Audience location and age match your customers.",
                    },
                    {
                        "criterion": "Platform fit",
                        "detail": f"Strong recent {platform} work in a {voice} style.",
                    },
                ],
            }
        )


def get_generator() -> BriefGenerator:
    mode = settings.BRIEF_GENERATOR
    has_key = bool(settings.ANTHROPIC_API_KEY)
    if mode == "demo" or (mode == "auto" and not has_key):
        return DemoBriefGenerator()
    if not has_key:
        raise GenerationUnavailable("ANTHROPIC_API_KEY is not configured")
    client = anthropic.Anthropic(
        api_key=settings.ANTHROPIC_API_KEY,
        timeout=settings.ANTHROPIC_TIMEOUT_SECONDS,
        max_retries=1,
    )
    return AnthropicBriefGenerator(client=client, model=settings.ANTHROPIC_MODEL)
