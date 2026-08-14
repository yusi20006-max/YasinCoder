import json
import urllib.error

import pytest

from routing import Router, RoutingError, classify_error


def http_error(code):
    return urllib.error.HTTPError("http://example", code, "error", {}, None)


def test_transient_failure_falls_back_once():
    models = {
        "primary": {"name": "primary", "type": "openai_compatible", "fallbacks": ["backup"]},
        "backup": {"name": "backup", "type": "openai_compatible"},
    }
    calls = []

    def ask(model):
        calls.append(model["name"])
        if model["name"] == "primary":
            raise TimeoutError("timed out")
        return "ok"

    result = Router(models.get).run(models["primary"], ask)
    assert result.output == "ok"
    assert result.selected == "backup"
    assert [a.outcome for a in result.attempts] == ["timeout", "success"]
    assert calls == ["primary", "backup"]


def test_quota_does_not_fallback():
    models = {
        "primary": {"name": "primary", "type": "openai_compatible", "fallbacks": ["backup"]},
        "backup": {"name": "backup", "type": "openai_compatible"},
    }
    calls = []

    def ask(model):
        calls.append(model["name"])
        raise http_error(429)

    with pytest.raises(RoutingError) as caught:
        Router(models.get).run(models["primary"], ask)

    assert caught.value.kind == "quota"
    assert len(caught.value.attempts) == 1
    assert calls == ["primary"]


def test_fallback_chain_is_loop_free():
    models = {
        "a": {"name": "a", "fallbacks": ["b"]},
        "b": {"name": "b", "fallbacks": ["a"]},
    }
    assert [m["name"] for m in Router(models.get).order(models["a"])] == ["a", "b"]


def test_offline_mode_never_adds_fallbacks():
    primary = {"name": "local", "offline": True, "fallbacks": ["cloud"]}
    calls = []

    def ask(model):
        calls.append(model["name"])
        raise TimeoutError("offline local unavailable")

    with pytest.raises(RoutingError):
        Router(lambda name: {"name": name}).run(primary, ask)
    assert calls == ["local"]


def test_error_classification():
    assert classify_error(http_error(429)) == "quota"
    assert classify_error(http_error(401)) == "auth"
    assert classify_error(http_error(503)) == "server"
    assert classify_error(http_error(404)) == "model"
