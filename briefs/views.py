import json
import re
import time
import uuid
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST, require_safe

from . import ratelimit
from .analytics import CLIENT_EVENTS, track
from .forms import BriefRequestForm
from .generators import GenerationError, GenerationFailed, get_generator
from .schemas import GOALS, PLATFORMS, TONES

_REQUEST_ID = re.compile(r"^[0-9a-f]{32}$")


def _error(status: int, code: str, message: str, **extra: Any) -> JsonResponse:
    return JsonResponse({"error": {"code": code, "message": message, **extra}}, status=status)


def _read_json(request: HttpRequest) -> dict[str, Any] | None:
    try:
        data = json.loads(request.body or b"")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


@require_safe
@ensure_csrf_cookie
def index(request: HttpRequest) -> HttpResponse:
    context = {"platforms": PLATFORMS, "goals": GOALS, "tones": TONES}
    return render(request, "briefs/index.html", context)


@require_safe
def healthz(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok", content_type="text/plain")


@require_POST
def generate_brief(request: HttpRequest) -> JsonResponse:
    ip = ratelimit.client_ip(request)
    if not ratelimit.allow("briefs", ip, settings.BRIEF_RATE_LIMIT_PER_MIN):
        return _error(
            429, "rate_limited", "You're generating briefs quickly. Wait a minute and try again."
        )

    data = _read_json(request)
    if data is None:
        return _error(400, "invalid_input", "Send the form as a JSON object.", fields={})

    form = BriefRequestForm(data=data)
    if not form.is_valid():
        fields = {name: [str(e) for e in errors] for name, errors in form.errors.items()}
        return _error(400, "invalid_input", "Check the highlighted fields.", fields=fields)

    inputs = form.to_inputs()
    request_id = uuid.uuid4().hex
    started = time.monotonic()
    source = "unknown"
    try:
        generator = get_generator()
        source = generator.source
        brief = generator.generate(inputs)
    except GenerationError as exc:
        code = (
            "generation_failed" if isinstance(exc, GenerationFailed) else "generation_unavailable"
        )
        status = 502 if isinstance(exc, GenerationFailed) else 503
        track(
            "brief_failed",
            request_id=request_id,
            source=source,
            code=code,
            latency_ms=round((time.monotonic() - started) * 1000),
        )
        return _error(status, code, exc.user_message)

    track(
        "brief_generated",
        request_id=request_id,
        source=source,
        platform=inputs.platform,
        goal=inputs.goal,
        tone=inputs.tone,
        has_product_note=bool(inputs.product_note),
        latency_ms=round((time.monotonic() - started) * 1000),
    )
    return JsonResponse(
        {"brief": brief.model_dump(), "meta": {"source": source, "request_id": request_id}}
    )


@require_POST
def log_event(request: HttpRequest) -> HttpResponse:
    if not ratelimit.allow("events", ratelimit.client_ip(request), 60):
        return _error(429, "rate_limited", "Too many events.")
    data = _read_json(request)
    if (
        data is None
        or data.get("event") not in CLIENT_EVENTS
        or not _REQUEST_ID.match(str(data.get("request_id", "")))
    ):
        return _error(400, "invalid_input", "Unknown event.")
    track(data["event"], request_id=data["request_id"])
    return HttpResponse(status=204)
