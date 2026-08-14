"""Cloudflare Workers AI adapter."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderAdapter, ProviderAuthenticationError, ProviderConfigurationError, ProviderRequestError, ProviderUnavailable


class CloudflareProvider(ProviderAdapter):
    provider_type = "cloudflare"
    offline = False

    def __init__(self, model: dict[str, Any] | None = None):
        model = dict(model or {})
        super().__init__(model)
        self.account_id = str(model.get("account_id", ""))
        self.api_token = str(model.get("api_token", ""))
        self.model_name = str(model.get("model") or model.get("name") or "")
        self.timeout = float(model.get("timeout", 120))

    def health(self) -> bool:
        return bool(self.account_id and self.api_token and self.model_name)

    def chat(self, prompt: str) -> str:
        if not self.account_id or not self.api_token or not self.model_name:
            raise ProviderConfigurationError("Cloudflare account, token and model must be configured")
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model_name}"
        payload = {"messages": [{"role": "user", "content": prompt}]}
        request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Authorization": "Bearer " + self.api_token, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderAuthenticationError("Cloudflare authentication failed", status=exc.code) from None
            raise ProviderRequestError(f"Cloudflare returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderUnavailable("Cloudflare is unavailable") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ProviderRequestError("Cloudflare returned invalid JSON") from None
        result = data.get("result") or {}
        if "response" in result:
            return str(result["response"])
        if isinstance(result, dict) and result.get("output"):
            return str(result["output"])
        raise ProviderRequestError("Cloudflare returned no model output")
