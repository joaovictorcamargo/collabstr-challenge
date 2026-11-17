"""Shared test data and fakes. Tests never call the real Claude API."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

VALID_INPUT: dict[str, str] = {
    "brand_name": "Glow Lab",
    "platform": "tiktok",
    "goal": "awareness",
    "tone": "playful",
    "product_note": "New vitamin C serum for sensitive skin",
}


def brief_payload(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "campaign_title": "Glow Lab: Glow Up in 15 Seconds",
        "summary": "A TikTok awareness push introducing Glow Lab's vitamin C serum.",
        "objective": "Reach 500k people aged 18-30 and grow profile visits by 20%.",
        "key_message": "Gentle vitamin C that sensitive skin actually likes.",
        "deliverables": ["1 TikTok video (15-30s)", "3 raw clips for Spark Ads"],
        "dos": ["Show the texture up close", "Film in natural light", "Tag @glowlab"],
        "donts": ["Make medical claims", "Use competitor products on screen"],
        "content_angles": [
            {"title": "Morning routine", "hook": "POV: 7am", "description": "Routine video."},
            {"title": "Myth vs fact", "hook": "Vitamin C stings?", "description": "Myth bust."},
            {"title": "Before/after", "hook": "Day 1 vs 14", "description": "Progress clip."},
        ],
        "creator_criteria": [
            {"criterion": "Niche", "detail": "Skincare or beauty creators."},
            {"criterion": "Audience", "detail": "Mostly 18-30, US based."},
            {"criterion": "Style", "detail": "Comfortable on camera, playful edits."},
        ],
    }
    data.update(overrides)
    return data


class FakeMessages:
    """Mimics `client.beta.messages` and records the kwargs of each call."""

    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


def fake_client(
    *, text: str | None = None, stop_reason: str = "end_turn", error: Exception | None = None
) -> Any:
    if text is None:
        text = json.dumps(brief_payload())
    content = [
        SimpleNamespace(type="thinking", thinking=""),
        SimpleNamespace(type="text", text=text),
    ]
    response = SimpleNamespace(stop_reason=stop_reason, content=content, stop_details=None)
    messages = FakeMessages(response=response, error=error)
    return SimpleNamespace(beta=SimpleNamespace(messages=messages), messages=messages)
