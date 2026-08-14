import json
import os
import urllib.error
import urllib.request

from providers.base import BaseProvider


class LocalProvider(BaseProvider):
    """Provider for the local YasinCoder AI Gateway.

    The gateway owns local model lifecycle (llama.cpp/Qwen) and can later
    route to additional local/remote models. YasinCoder only talks to its
    stable HTTP contract.
    """

    name = "local"

    def __init__(self):
        self.base_url = os.getenv(
            "YASIN_GATEWAY_URL",
            "http://127.0.0.1:18765",
        ).rstrip("/")
        self.timeout = float(os.getenv("YASIN_GATEWAY_TIMEOUT", "120"))

    def chat(self, prompt):
        payload = json.dumps({"prompt": prompt}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/qwen",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            return f"Local Gateway Error: {exc}"

        if not data.get("ok"):
            return data.get("error") or "Local Gateway returned an unsuccessful response."

        return data.get("output", "")
