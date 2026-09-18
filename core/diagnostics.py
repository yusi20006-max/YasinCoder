"""Bounded, secret-safe diagnostics for supported YasinCoder interfaces."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .redaction import redact, redact_exception


MAX_MESSAGE = 512
MAX_DETAIL = 2048
CATEGORIES = {
    "configuration",
    "authentication",
    "permission",
    "workspace",
    "provider",
    "network",
    "timeout",
    "test",
    "github",
    "internal",
}


@dataclass(frozen=True)
class Diagnostic:
    category: str
    message: str
    detail: str = ""
    retryable: bool = False
    code: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "code": self.code or self.category,
            "message": self.message,
            "detail": self.detail,
            "retryable": self.retryable,
        }


def _bounded(value: object, limit: int) -> str:
    text = str(redact(str(value)))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def diagnostic(
    category: str,
    message: object,
    *,
    detail: object = "",
    retryable: bool = False,
    code: str = "",
    context: Mapping[str, object] | None = None,
) -> Diagnostic:
    normalized = category if category in CATEGORIES else "internal"
    context_text = ""
    if context:
        safe = redact(dict(context))
        context_text = _bounded(safe, MAX_DETAIL)
    detail_text = _bounded(detail, MAX_DETAIL)
    if context_text:
        detail_text = f"{detail_text} | context={context_text}" if detail_text else f"context={context_text}"
    return Diagnostic(
        category=normalized,
        message=_bounded(message, MAX_MESSAGE),
        detail=detail_text,
        retryable=bool(retryable),
        code=_bounded(code or normalized, 96),
    )


def from_exception(exc: BaseException, *, category: str = "internal", retryable: bool = False) -> Diagnostic:
    kind = getattr(exc, "kind", None)
    mapped = {
        "authentication": "authentication",
        "configuration": "configuration",
        "unavailable": "network",
        "request": "provider",
    }.get(kind, category)
    return diagnostic(
        mapped,
        str(exc) or exc.__class__.__name__,
        detail=redact_exception(exc),
        retryable=retryable,
        code=str(kind or mapped),
    )
