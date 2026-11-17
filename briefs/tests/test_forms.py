import pytest

from briefs.forms import BriefRequestForm
from briefs.schemas import BriefInputs

from .factories import VALID_INPUT


def test_valid_input_produces_brief_inputs():
    form = BriefRequestForm(data=VALID_INPUT)
    assert form.is_valid(), form.errors
    inputs = form.to_inputs()
    assert inputs == BriefInputs(
        brand_name="Glow Lab",
        platform="tiktok",
        goal="awareness",
        tone="playful",
        product_note="New vitamin C serum for sensitive skin",
    )


def test_product_note_is_optional():
    data = {**VALID_INPUT}
    del data["product_note"]
    form = BriefRequestForm(data=data)
    assert form.is_valid(), form.errors
    assert form.to_inputs().product_note == ""


@pytest.mark.parametrize("field", ["brand_name", "platform", "goal", "tone"])
def test_required_fields(field):
    data = {**VALID_INPUT, field: ""}
    form = BriefRequestForm(data=data)
    assert not form.is_valid()
    assert field in form.errors


@pytest.mark.parametrize(
    ("field", "value"),
    [("platform", "youtube"), ("goal", "sales"), ("tone", "angry")],
)
def test_rejects_unknown_choices(field, value):
    form = BriefRequestForm(data={**VALID_INPUT, field: value})
    assert not form.is_valid()
    assert field in form.errors


def test_brand_name_is_trimmed_and_whitespace_collapsed():
    form = BriefRequestForm(data={**VALID_INPUT, "brand_name": "  Glow \n  Lab  "})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["brand_name"] == "Glow Lab"


@pytest.mark.parametrize("value", ["A", "x" * 61, "   "])
def test_brand_name_length_bounds(value):
    form = BriefRequestForm(data={**VALID_INPUT, "brand_name": value})
    assert not form.is_valid()
    assert "brand_name" in form.errors


def test_product_note_max_length():
    form = BriefRequestForm(data={**VALID_INPUT, "product_note": "x" * 281})
    assert not form.is_valid()
    assert "product_note" in form.errors


def test_control_characters_are_removed():
    form = BriefRequestForm(data={**VALID_INPUT, "product_note": "serum\x07\x1b for skin"})
    assert form.is_valid(), form.errors
    assert form.cleaned_data["product_note"] == "serum for skin"
