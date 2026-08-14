"""Deterministic routing and fallback policy for YasinCoder.

Routing is configuration-driven. Only transient provider failures are eligible
for fallback; quota/auth/model/configuration errors stop the chain immediately.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


TRANSIENT = {"timeout", "network", "server"}
NON_TRANSIENT = {"quota", "auth", "model", "configuration", "invalid_request"}


class RoutingError(RuntimeError):
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message


def classify_error(exc: Exception) -> str:
    """Classify provider failures without exposing credentials or raw payloads."""
    import urllib.error

    if isinstance(exc, (TimeoutError, TimeoutError)):
        return "timeout"
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code == 401 or exc.code == 403:
            return "auth"
        if exc.code == 429:
            return "quota"
        if exc.code in {408, 409, 425, 500, 502, 503, 504}:
            return "server"
        if exc.code == 404:
            return "model"
        return "provider"
    if isinstance(exc, urllib.error.URLError):
        return "network"

    text = str(exc).lower()
    if any(token in text for token in ("quota", "rate limit", "429", "too many requests")):
        return "quota"
    if any(token in text for token in ("unauthorized", "forbidden", "api key", "authentication")):
        return "auth"
    if any(token in text for token in ("timeout", "timed out")):
        return "timeout"
    if any(token in text for token in ("connection", "network", "dns", "fetch failed")):
        return "network"
    if any(token in text for token in ("model not found", "unknown model", "does not exist")):
        return "model"
    return "provider"


@dataclass
class RouteAttempt:
    model: str
    outcome: str
    error: str | None = None


@dataclass
class RoutingResult:
    output: str
    selected: str
    attempts: list[RouteAttempt] = field(default_factory=list)


class Router:
    """Execute an ordered, loop-free fallback chain."""

    def __init__(self, resolver: Callable[[str], dict | None]):
        self.resolver = resolver

    def order(self, primary: dict, configured: Iterable[str] | None = None) -> list[dict]:
        names = [primary.get("name", "")]
        names.extend(str(x) for x in (configured or primary.get("fallbacks", [])) if str(x))
        result: list[dict] = []
        seen: set[str] = set()
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            model = self.resolver(name)
            if model:
                result.append(model)
        return result

    def run(self, primary: dict, ask: Callable[[dict], str]) -> RoutingResult:
        if primary.get("offline") is True:
            chain = [primary]
        else:
            chain = self.order(primary)

        attempts: list[RouteAttempt] = []
        for model in chain:
            name = str(model.get("name") or model.get("model") or "unknown")
            try:
                output = ask(model)
                attempts.append(RouteAttempt(name, "success"))
                return RoutingResult(str(output), name, attempts)
            except Exception as exc:
                kind = classify_error(exc)
                attempts.append(RouteAttempt(name, kind, kind if kind != "provider" else "provider_error"))
                if kind not in TRANSIENT:
                    raise RoutingError(kind, f"Provider '{name}' failed: {kind}") from exc

        last = attempts[-1] if attempts else None
        raise RoutingError(last.outcome if last else "configuration", "No provider succeeded")
