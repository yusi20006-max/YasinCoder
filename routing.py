"""Deterministic routing and fallback policy for YasinCoder.

Only failures explicitly classified as safe-to-fallback are allowed to move to
another provider. Authentication and configuration failures stop immediately.
Routing diagnostics contain only sanitized model names and normalized error
categories; provider payloads and credentials are never propagated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable


# These failures can safely select the next configured provider without retrying
# the same provider, which avoids retry storms. Quota/rate-limit failures are
# treated as fallback-eligible but are never retried against the same provider.
TRANSIENT = {"timeout", "network", "server", "quota", "rate_limit", "unavailable"}


class RoutingError(RuntimeError):
    def __init__(self, kind: str, message: str, attempts: list["RouteAttempt"] | None = None):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.attempts = attempts or []


def _provider_error_kind(exc: Exception) -> str | None:
    """Map YasinCoder provider errors to routing categories without raw details."""
    kind = getattr(exc, "kind", None)
    status = getattr(exc, "status", None)
    if kind == "authentication":
        return "auth"
    if kind == "configuration":
        return "configuration"
    if kind == "unavailable":
        return "unavailable"
    if kind == "request":
        if status == 429:
            return "rate_limit"
        if status in {408, 409, 425, 500, 502, 503, 504}:
            return "server"
        if status in {401, 403}:
            return "auth"
        if status == 404:
            return "model"
        return "provider"
    return None


def classify_error(exc: Exception) -> str:
    """Classify provider failures without exposing credentials or raw payloads."""
    provider_kind = _provider_error_kind(exc)
    if provider_kind:
        return provider_kind

    import urllib.error

    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in {401, 403}:
            return "auth"
        if exc.code == 429:
            return "rate_limit"
        if exc.code in {408, 409, 425, 500, 502, 503, 504}:
            return "server"
        if exc.code == 404:
            return "model"
        return "provider"
    if isinstance(exc, urllib.error.URLError):
        return "network"

    text = str(exc).lower()
    if any(token in text for token in ("quota", "rate limit", "429", "too many requests")):
        return "rate_limit"
    if any(token in text for token in ("unauthorized", "forbidden", "api key", "authentication")):
        return "auth"
    if any(token in text for token in ("configuration", "not configured", "missing api")):
        return "configuration"
    if any(token in text for token in ("timeout", "timed out")):
        return "timeout"
    if any(token in text for token in ("connection", "network", "dns", "fetch failed")):
        return "network"
    if any(token in text for token in ("model not found", "unknown model", "does not exist")):
        return "model"
    return "provider"


def _safe_model_name(model: dict) -> str:
    """Return a bounded, credential-free diagnostic identifier."""
    value = str(model.get("name") or model.get("model") or "unknown")
    return value[:128].replace("\n", " ").replace("\r", " ")


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
        names = [_safe_model_name(primary)]
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
        # Explicit offline providers are intentionally isolated from online
        # fallbacks: silently sending local work to a remote provider violates
        # the user's offline intent.
        chain = [primary] if primary.get("offline") is True else self.order(primary)
        attempts: list[RouteAttempt] = []
        for model in chain:
            name = _safe_model_name(model)
            try:
                output = ask(model)
                attempts.append(RouteAttempt(name, "success"))
                return RoutingResult(str(output), name, attempts)
            except Exception as exc:
                kind = classify_error(exc)
                attempts.append(RouteAttempt(name, kind, kind))
                # Auth/config/model failures are not safe to retry elsewhere by
                # default. A quota/server/network failure advances immediately
                # to the next configured provider, never retrying the same one.
                if kind not in TRANSIENT:
                    raise RoutingError(kind, f"Provider '{name}' failed: {kind}", attempts) from exc

        last = attempts[-1] if attempts else None
        raise RoutingError(last.outcome if last else "configuration", "No provider succeeded", attempts)
