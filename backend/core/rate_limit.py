"""IP-based rate limiter for the API."""

from __future__ import annotations

from starlette.requests import Request

from slowapi import Limiter
from slowapi.util import get_remote_address


def _ip_key(request: Request) -> str:
    """Rate limit key: client IP, respecting X-Forwarded-For when behind a proxy."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_ip_key, default_limits=["30/minute"])
