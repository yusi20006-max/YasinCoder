"""Canonical request/response/error contract for the YasinCoder gateway.

The contract is intentionally provider-neutral. Provider adapters translate their
native payloads into these shapes; callers never depend on provider-specific
fields or exception text.
"""
from __future__ import annotations

from typing import Any

MAX_MESSAGES = 128
MAX_MODEL_NAME = 256


def validate_chat_request(payload: Any) -> tuple[str | None, list[dict[str, Any]]]:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object")
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages or len(messages) > MAX_MESSAGES:
        raise ValueError(f"messages must be a non-empty list with at most {MAX_MESSAGES} items")
    for message in messages:
        if not isinstance(message, dict) or not isinstance(message.get("role"), str):
            raise ValueError("each message must contain a string role")
        if not isinstance(message.get("content", ""), (str, list)):
            raise ValueError("message content must be text or structured content")
    model = payload.get("model")
    if model is not None and (not isinstance(model, str) or not model.strip() or len(model) > MAX_MODEL_NAME):
        raise ValueError("model must be a non-empty short string")
    return model, messages


def chat_response(*, request_id: str, model: str, content: str, created: int,
                  routing: dict[str, Any] | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {
        "id": request_id,
        "object": "chat.completion",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
    if routing is not None:
        response["routing"] = routing
    return response


def error_response(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}
