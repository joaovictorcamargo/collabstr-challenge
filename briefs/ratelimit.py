"""Tiny fixed-window rate limiter on Django's cache."""

import time

from django.core.cache import cache
from django.http import HttpRequest


def client_ip(request: HttpRequest) -> str:
    """Best-effort client IP.

    Behind one reverse proxy (Render), the proxy appends the real client IP as the
    *last* X-Forwarded-For entry; anything to the left is client-controlled.
    """
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return str(forwarded).split(",")[-1].strip()
    return str(request.META.get("REMOTE_ADDR", "unknown"))


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
