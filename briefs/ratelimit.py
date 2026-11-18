"""Tiny fixed-window rate limiter on Django's cache."""

import ipaddress
import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


def _valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request: HttpRequest) -> str:
    """Client IP for rate limiting, in order of trust.

    1. CLIENT_IP_HEADER: a header the edge proxy *overwrites* (Cloudflare's
       CF-Connecting-IP on Render). Only set this when that proxy is always in front,
       otherwise clients could send the header themselves.
    2. X-Forwarded-For with TRUSTED_PROXY_COUNT hops: each trusted proxy appends the
       address it saw, so the client is the N-th entry from the right.
    3. REMOTE_ADDR.
    """
    remote = str(request.META.get("REMOTE_ADDR", "unknown"))
    header = settings.CLIENT_IP_HEADER
    if header and (ip := _valid_ip(str(request.META.get(header, "")))):
        return ip
    hops = settings.TRUSTED_PROXY_COUNT
    if hops <= 0:
        return remote
    entries = [e.strip() for e in str(request.META.get("HTTP_X_FORWARDED_FOR", "")).split(",")]
    entries = [e for e in entries if e]
    if len(entries) >= hops and (ip := _valid_ip(entries[-hops])):
        return ip
    return remote


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
