import pytest
from pydantic import ValidationError

from briefs.schemas import GOALS, PLATFORMS, TONES, Brief, brief_json_schema

from .factories import brief_payload


def test_valid_payload_parses():
    brief = Brief.model_validate(brief_payload())
    assert brief.campaign_title.startswith("Glow Lab")
    assert len(brief.content_angles) == 3
    assert brief.creator_criteria[0].criterion == "Niche"


def test_missing_section_is_rejected():
    payload = brief_payload()
    del payload["creator_criteria"]
    with pytest.raises(ValidationError):
        Brief.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("content_angles", []),
        ("creator_criteria", []),
        ("summary", ""),
        ("dos", ["x"] * 9),
    ],
)
def test_out_of_bounds_values_are_rejected(field, value):
    with pytest.raises(ValidationError):
        Brief.model_validate(brief_payload(**{field: value}))


def test_extra_keys_are_rejected():
    with pytest.raises(ValidationError):
        Brief.model_validate(brief_payload(unexpected="x"))


def test_json_schema_is_strict_for_structured_outputs():
    schema = brief_json_schema()

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert set(node["required"]) == set(node["properties"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(schema)
    assert "$defs" not in schema, "schema should be inlined for the API"


def test_choice_labels():
    assert PLATFORMS == {"instagram": "Instagram", "tiktok": "TikTok", "ugc": "UGC"}
    assert GOALS == {
        "awareness": "Awareness",
        "conversions": "Conversions",
        "content_assets": "Content Assets",
    }
    assert TONES == {"professional": "Professional", "friendly": "Friendly", "playful": "Playful"}
