"""Centralized redaction for credentials and sensitive runtime data."""
from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Any

_SECRET_PATTERNS = (
    re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^\s'\"]{8,}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{16,}"),
)
_SENSITIVE_KEYS = {"api_key", "apikey", "authorization", "token", "access_token", "refresh_token", "secret", "password", "credential", "credentials"}


def configured_secrets() -> tuple[str, ...]:
    values = []
    for key, value in os.environ.items():
        if any(word in key.lower() for word in ("key", "token", "secret", "password", "credential")) and value:
            values.append(value)
    return tuple(sorted(set(values), key=len, reverse=True))


def redact(value: Any, *, secrets: tuple[str, ...] | None = None) -> Any:
    """Redact known secrets from strings and recursively from mappings/sequences."""
    if isinstance(value, str):
        result = value
        for secret in secrets if secrets is not None else configured_secrets():
            if len(secret) >= 4:
                result = result.replace(secret, "[REDACTED]")
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub("[REDACTED]", result)
        return result
    if isinstance(value, Mapping):
        return {str(k): "[REDACTED]" if str(k).lower() in _SENSITIVE_KEYS else redact(v, secrets=secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(redact(v, secrets=secrets) for v in value)
    return value


def redact_exception(exc: BaseException) -> str:
    return str(redact(str(exc)))
