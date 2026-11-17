import json

import anthropic
import httpx2
import pytest

from briefs.generators import (
    AnthropicBriefGenerator,
    DemoBriefGenerator,
    GenerationFailed,
    GenerationUnavailable,
    get_generator,
)
from briefs.schemas import GOALS, PLATFORMS, TONES, Brief, BriefInputs

from .factories import brief_payload, fake_client

INPUTS = BriefInputs(
    brand_name="Glow Lab", platform="tiktok", goal="awareness", tone="playful", product_note=""
)
REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def status_error(cls, status):
    response = httpx2.Response(status, request=REQUEST)
    return cls("boom", response=response, body=None)


# --- Anthropic generator -------------------------------------------------


def test_anthropic_success_returns_validated_brief():
    client = fake_client()
    brief = AnthropicBriefGenerator(client=client, model="claude-opus-5-5").generate(INPUTS)
    assert isinstance(brief, Brief)
    assert brief.campaign_title == brief_payload()["campaign_title"]


def test_anthropic_request_shape():
    client = fake_client()
    AnthropicBriefGenerator(client=client, model="claude-test").generate(INPUTS)
    call = client.beta.messages.calls[0]
    assert call["model"] == "claude-test"
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["output_config"]["effort"] == "low"
    assert call["fallbacks"] == "default"
    assert "server-side-fallback-2026-07-01" in call["betas"]
    assert call["messages"][0]["role"] == "user"
    assert "Glow Lab" in call["messages"][0]["content"]
    assert call["system"]


def test_refusal_is_generation_failed():
    client = fake_client(stop_reason="refusal", text="")
    with pytest.raises(GenerationFailed):
        AnthropicBriefGenerator(client=client, model="m").generate(INPUTS)


def test_truncated_output_is_generation_failed():
    client = fake_client(stop_reason="max_tokens", text='{"campaign_title": "x"')
    with pytest.raises(GenerationFailed):
        AnthropicBriefGenerator(client=client, model="m").generate(INPUTS)


def test_invalid_json_is_generation_failed():
    client = fake_client(text="not json")
    with pytest.raises(GenerationFailed):
        AnthropicBriefGenerator(client=client, model="m").generate(INPUTS)


def test_schema_mismatch_is_generation_failed():
    client = fake_client(text=json.dumps({"campaign_title": "only this"}))
    with pytest.raises(GenerationFailed):
        AnthropicBriefGenerator(client=client, model="m").generate(INPUTS)


@pytest.mark.parametrize(
    "error",
    [
        anthropic.APITimeoutError(request=REQUEST),
        anthropic.APIConnectionError(request=REQUEST),
        status_error(anthropic.RateLimitError, 429),
        status_error(anthropic.InternalServerError, 500),
        status_error(anthropic.AuthenticationError, 401),
    ],
)
def test_api_errors_are_generation_unavailable(error):
    client = fake_client(error=error)
    with pytest.raises(GenerationUnavailable):
        AnthropicBriefGenerator(client=client, model="m").generate(INPUTS)


def test_bad_request_is_generation_failed():
    client = fake_client(error=status_error(anthropic.BadRequestError, 400))
    with pytest.raises(GenerationFailed):
        AnthropicBriefGenerator(client=client, model="m").generate(INPUTS)


# --- Demo generator ------------------------------------------------------


@pytest.mark.parametrize("platform", list(PLATFORMS))
@pytest.mark.parametrize("goal", list(GOALS))
@pytest.mark.parametrize("tone", list(TONES))
def test_demo_generator_always_returns_valid_brief(platform, goal, tone):
    inputs = BriefInputs(
        brand_name="Acme", platform=platform, goal=goal, tone=tone, product_note="trail shoes"
    )
    brief = DemoBriefGenerator().generate(inputs)
    assert isinstance(brief, Brief)
    assert "Acme" in brief.campaign_title
    assert PLATFORMS[platform] in brief.summary


# --- Factory -------------------------------------------------------------


def test_get_generator_auto_without_key_is_demo(settings):
    settings.BRIEF_GENERATOR = "auto"
    settings.ANTHROPIC_API_KEY = ""
    assert isinstance(get_generator(), DemoBriefGenerator)


def test_get_generator_auto_with_key_is_anthropic(settings):
    settings.BRIEF_GENERATOR = "auto"
    settings.ANTHROPIC_API_KEY = "sk-test"
    assert isinstance(get_generator(), AnthropicBriefGenerator)


def test_get_generator_forced_anthropic_without_key_is_unavailable(settings):
    settings.BRIEF_GENERATOR = "anthropic"
    settings.ANTHROPIC_API_KEY = ""
    with pytest.raises(GenerationUnavailable):
        get_generator()
