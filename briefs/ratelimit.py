"""Tiny fixed-window rate limiter on Django's cache."""

import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


def client_ip(request: HttpRequest) -> str:
    """Client IP for rate limiting.

    Each trusted reverse proxy appends the address it received the request from to
    X-Forwarded-For, so with N trusted proxies the real client is the N-th entry from
    the right; everything further left is client-controlled. With no trusted proxy
    (TRUSTED_PROXY_COUNT=0) the header is ignored entirely.
    """
    hops = settings.TRUSTED_PROXY_COUNT
    remote = str(request.META.get("REMOTE_ADDR", "unknown"))
    if hops <= 0:
        return remote
    entries = [e.strip() for e in str(request.META.get("HTTP_X_FORWARDED_FOR", "")).split(",")]
    entries = [e for e in entries if e]
    return entries[-hops] if len(entries) >= hops else remote


def allow(scope: str, key: str, limit: int, window_seconds: int = 60) -> bool:
    """Return True if this call is within `limit` calls per window for (scope, key)."""
    bucket = int(time.time() // window_seconds)
    cache_key = f"rl:{scope}:{key}:{bucket}"
    cache.add(cache_key, 0, timeout=window_seconds * 2)
    try:
        count = cache.incr(cache_key)
    except ValueError:  # key expired between add and incr
        cache.set(cache_key, 1, timeout=window_seconds * 2)
        count = 1
    return count <= limit
