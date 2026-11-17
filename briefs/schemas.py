"""Brief input/output types. Keep in sync with the `Brief` schema in docs/spec.md."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

PLATFORMS: dict[str, str] = {"instagram": "Instagram", "tiktok": "TikTok", "ugc": "UGC"}
GOALS: dict[str, str] = {
    "awareness": "Awareness",
    "conversions": "Conversions",
    "content_assets": "Content Assets",
}
TONES: dict[str, str] = {
    "professional": "Professional",
    "friendly": "Friendly",
    "playful": "Playful",
}


@dataclass(frozen=True)
class BriefInputs:
    brand_name: str
    platform: str
    goal: str
    tone: str
    product_note: str = ""

    @property
    def platform_label(self) -> str:
        return PLATFORMS[self.platform]

    @property
    def goal_label(self) -> str:
        return GOALS[self.goal]

    @property
    def tone_label(self) -> str:
        return TONES[self.tone]


Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContentAngle(_Strict):
    title: Text
    hook: Text
    description: Text


class CreatorCriterion(_Strict):
    criterion: Text
    detail: Text


class Brief(_Strict):
    campaign_title: Text
    summary: Text
    objective: Text
    key_message: Text
    deliverables: list[Text] = Field(min_length=1, max_length=6)
    dos: list[Text] = Field(min_length=1, max_length=8)
    donts: list[Text] = Field(min_length=1, max_length=8)
    content_angles: list[ContentAngle] = Field(min_length=3, max_length=6)
    creator_criteria: list[CreatorCriterion] = Field(min_length=3, max_length=8)


def _obj(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


_STR: dict[str, Any] = {"type": "string"}


def _str_list(description: str) -> dict[str, Any]:
    return {"type": "array", "items": _STR, "description": description}


def brief_json_schema() -> dict[str, Any]:
    """JSON schema sent to Claude's structured outputs.

    Written by hand (not generated from Pydantic) so it only uses keywords the API supports.
    Size limits are stated in the prompt and enforced by `Brief` on the way back.
    """
    return _obj(
        {
            "campaign_title": {**_STR, "description": "Short, catchy campaign name."},
            "summary": {**_STR, "description": "2-3 sentence overview of the campaign."},
            "objective": {**_STR, "description": "Goal with one measurable success signal."},
            "key_message": {**_STR, "description": "The one thing viewers should remember."},
            "deliverables": _str_list("2-4 platform-specific content deliverables."),
            "dos": _str_list("3-5 practical do's for creators."),
            "donts": _str_list("2-4 don'ts for creators."),
            "content_angles": {
                "type": "array",
                "description": "3-5 distinct content angles.",
                "items": _obj({"title": _STR, "hook": _STR, "description": _STR}),
            },
            "creator_criteria": {
                "type": "array",
                "description": "3-6 creator selection criteria.",
                "items": _obj({"criterion": _STR, "detail": _STR}),
            },
        }
    )
