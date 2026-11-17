import json
import logging

import pytest
from django.core.cache import cache
from django.test import Client
from django.urls import reverse

from briefs import views
from briefs.generators import DemoBriefGenerator, GenerationFailed, GenerationUnavailable
from briefs.schemas import Brief

from .factories import VALID_INPUT, brief_payload

API = "/api/briefs/"
EVENTS = "/api/events/"


class StubGenerator:
    source = "anthropic"

    def __init__(self, result=None, error=None):
        self.result = result or Brief.model_validate(brief_payload())
        self.error = error
        self.calls = []

    def generate(self, inputs):
        self.calls.append(inputs)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def stub(monkeypatch):
    generator = StubGenerator()
    monkeypatch.setattr(views, "get_generator", lambda: generator)
    return generator


def post_json(client, url, payload, **extra):
    body = payload if isinstance(payload, str) else json.dumps(payload)
    return client.post(url, data=body, content_type="application/json", **extra)


# --- Page ----------------------------------------------------------------


def test_index_renders_form_and_sets_csrf_cookie(client):
    response = client.get(reverse("briefs:index"))
    assert response.status_code == 200
    html = response.content.decode()
    for text in (
        "Brand name",
        "Instagram",
        "TikTok",
        "UGC",
        "Awareness",
        "Conversions",
        "Content Assets",
        "Professional",
        "Friendly",
        "Playful",
        "Generate brief",
    ):
        assert text in html
    assert "csrftoken" in response.cookies


def test_favicon_probe_is_not_a_404(client):
    assert client.get("/favicon.ico").status_code == 204


def test_healthcheck(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.content == b"ok"


# --- Briefs API ----------------------------------------------------------


def test_generate_success(client, stub, caplog):
    with caplog.at_level(logging.INFO, logger="briefs.analytics"):
        response = post_json(client, API, VALID_INPUT)
    assert response.status_code == 200
    data = response.json()
    assert data["brief"]["campaign_title"] == brief_payload()["campaign_title"]
    assert data["meta"]["source"] == "anthropic"
    assert len(data["meta"]["request_id"]) == 32
    assert stub.calls[0].brand_name == "Glow Lab"
    assert any('"event": "brief_generated"' in r.getMessage() for r in caplog.records)


def test_generate_validation_errors(client, stub):
    response = post_json(client, API, {**VALID_INPUT, "platform": "myspace", "brand_name": ""})
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "invalid_input"
    assert set(error["fields"]) == {"platform", "brand_name"}
    assert stub.calls == []


@pytest.mark.parametrize("body", ["not json", "[]", '"string"'])
def test_generate_malformed_body(client, stub, body):
    response = post_json(client, API, body)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_input"


def test_generate_requires_post(client):
    assert client.get(API).status_code == 405


def test_generate_enforces_csrf(stub):
    csrf_client = Client(enforce_csrf_checks=True)
    response = post_json(csrf_client, API, VALID_INPUT)
    assert response.status_code == 403

    csrf_client.get("/")
    token = csrf_client.cookies["csrftoken"].value
    response = post_json(csrf_client, API, VALID_INPUT, HTTP_X_CSRFTOKEN=token)
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("error", "status", "code"),
    [
        (GenerationFailed("bad output"), 502, "generation_failed"),
        (GenerationUnavailable("timeout"), 503, "generation_unavailable"),
    ],
)
def test_generate_maps_generator_errors(client, monkeypatch, error, status, code):
    monkeypatch.setattr(views, "get_generator", lambda: StubGenerator(error=error))
    response = post_json(client, API, VALID_INPUT)
    assert response.status_code == status
    body = response.json()["error"]
    assert body["code"] == code
    assert body["message"]
    assert "timeout" not in body["message"].lower() or status == 503


def test_generate_when_generator_not_configured(client, monkeypatch):
    def broken():
        raise GenerationUnavailable("no key")

    monkeypatch.setattr(views, "get_generator", broken)
    response = post_json(client, API, VALID_INPUT)
    assert response.status_code == 503


def test_generate_rate_limited(client, stub, settings):
    settings.BRIEF_RATE_LIMIT_PER_MIN = 2
    assert post_json(client, API, VALID_INPUT).status_code == 200
    assert post_json(client, API, VALID_INPUT).status_code == 200
    response = post_json(client, API, VALID_INPUT)
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "rate_limited"
    assert len(stub.calls) == 2


def test_daily_cap_stops_generation_across_clients(client, stub, settings):
    settings.BRIEF_DAILY_LIMIT = 2
    settings.TRUSTED_PROXY_COUNT = 1
    for ip in ("1.1.1.1", "2.2.2.2"):
        assert post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR=ip).status_code == 200
    response = post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR="3.3.3.3")
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "daily_limit_reached"
    assert len(stub.calls) == 2


def test_invalid_requests_do_not_use_daily_cap(client, stub, settings):
    settings.BRIEF_DAILY_LIMIT = 1
    assert post_json(client, API, {**VALID_INPUT, "tone": "angry"}).status_code == 400
    assert post_json(client, API, VALID_INPUT).status_code == 200


def test_healthcheck_is_exempt_from_https_redirect(client, settings):
    settings.SECURE_SSL_REDIRECT = True
    assert client.get("/healthz").status_code == 200
    assert client.get("/").status_code == 301


def test_rate_limit_ignores_forwarded_for_without_trusted_proxy(client, stub, settings):
    settings.BRIEF_RATE_LIMIT_PER_MIN = 1
    settings.TRUSTED_PROXY_COUNT = 0
    first = post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR="1.1.1.1")
    rotated = post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR="2.2.2.2")
    assert first.status_code == 200
    assert rotated.status_code == 429  # a fake header can't buy a fresh bucket


def test_rate_limit_uses_ip_added_by_trusted_proxy(client, stub, settings):
    settings.BRIEF_RATE_LIMIT_PER_MIN = 1
    settings.TRUSTED_PROXY_COUNT = 1
    first = post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR="1.1.1.1, 9.9.9.9")
    spoofed = post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR="2.2.2.2, 9.9.9.9")
    other = post_json(client, API, VALID_INPUT, HTTP_X_FORWARDED_FOR="8.8.8.8")
    assert first.status_code == 200
    assert spoofed.status_code == 429  # same real client, spoofed left-most entry
    assert other.status_code == 200


def test_generate_rejects_non_string_values(client, stub):
    response = post_json(client, API, {**VALID_INPUT, "brand_name": ["Glow", "Lab"]})
    assert response.status_code == 400
    assert "brand_name" in response.json()["error"]["fields"]
    assert stub.calls == []


def test_page_sends_content_security_policy(client):
    csp = client.get("/").headers["Content-Security-Policy"]
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


def test_demo_source_is_reported(client, monkeypatch):
    monkeypatch.setattr(views, "get_generator", DemoBriefGenerator)
    response = post_json(client, API, VALID_INPUT)
    assert response.status_code == 200
    assert response.json()["meta"]["source"] == "demo"


# --- Events API ----------------------------------------------------------


def test_event_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="briefs.analytics"):
        response = post_json(client, EVENTS, {"event": "brief_copied", "request_id": "a" * 32})
    assert response.status_code == 204
    assert any('"event": "brief_copied"' in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize(
    "payload",
    [
        {"event": "hacked", "request_id": "a" * 32},
        {"event": "brief_copied", "request_id": "<script>"},
        {"event": "brief_copied"},
        "nope",
    ],
)
def test_event_rejects_bad_payload(client, payload):
    assert post_json(client, EVENTS, payload).status_code == 400
