"""Security policy helpers for the YasinCoder gateway.

The gateway is local-only by default. Remote access and browser origins are
opt-in through environment variables. Secrets are never returned by these
helpers and API authentication uses a constant-time comparison.
"""
from __future__ import annotations

import hmac
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SecurityPolicy:
    api_key: str = ""
    allowed_origins: tuple[str, ...] = ()
    max_body_bytes: int = 1_048_576

    @classmethod
    def from_env(cls) -> "SecurityPolicy":
        raw_origins = os.getenv("YASIN_ALLOWED_ORIGINS", "").strip()
        origins = tuple(x.strip() for x in raw_origins.split(",") if x.strip())
        try:
            max_body = max(1024, int(os.getenv("YASIN_MAX_BODY_BYTES", "1048576")))
        except ValueError:
            max_body = 1_048_576
        return cls(os.getenv("YASIN_API_KEY", ""), origins, max_body)

    def authenticate(self, supplied: str | None) -> bool:
        if not self.api_key:
            return True
        return bool(supplied) and hmac.compare_digest(supplied, self.api_key)

    def origin_allowed(self, origin: str | None) -> bool:
        if not origin:
            return True
        return not self.allowed_origins or origin in self.allowed_origins

    def public_headers(self, origin: str | None = None) -> dict[str, str]:
        headers = {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer"}
        if origin and origin in self.allowed_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        return headers


DEFAULT_SECURITY_POLICY = SecurityPolicy.from_env()
