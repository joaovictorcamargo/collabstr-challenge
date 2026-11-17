import re
from typing import Any

from django import forms

from .schemas import GOALS, PLATFORMS, TONES, BriefInputs

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")


def _clean_text(value: str) -> str:
    return _WHITESPACE.sub(" ", _CONTROL_CHARS.sub("", value)).strip()


class BriefRequestForm(forms.Form):
    brand_name = forms.CharField(
        min_length=2,
        max_length=60,
        error_messages={
            "required": "Enter your brand name.",
            "min_length": "Brand name needs at least 2 characters.",
            "max_length": "Keep the brand name under 60 characters.",
        },
    )
    platform = forms.ChoiceField(
        choices=list(PLATFORMS.items()),
        error_messages={"required": "Choose a platform.", "invalid_choice": "Choose a platform."},
    )
    goal = forms.ChoiceField(
        choices=list(GOALS.items()),
        error_messages={"required": "Choose a goal.", "invalid_choice": "Choose a goal."},
    )
    tone = forms.ChoiceField(
        choices=list(TONES.items()),
        error_messages={"required": "Choose a tone.", "invalid_choice": "Choose a tone."},
    )
    product_note = forms.CharField(
        required=False,
        max_length=280,
        error_messages={"max_length": "Keep this under 280 characters."},
    )

    def clean_brand_name(self) -> str:
        value = _clean_text(self.cleaned_data["brand_name"])
        if len(value) < 2:
            raise forms.ValidationError("Brand name needs at least 2 characters.")
        return value

    def clean_product_note(self) -> str:
        return _clean_text(self.cleaned_data.get("product_note") or "")

    def to_inputs(self) -> BriefInputs:
        data: dict[str, Any] = self.cleaned_data
        return BriefInputs(
            brand_name=data["brand_name"],
            platform=data["platform"],
            goal=data["goal"],
            tone=data["tone"],
            product_note=data.get("product_note", ""),
        )
