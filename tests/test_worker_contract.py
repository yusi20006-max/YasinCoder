import unittest
from pathlib import Path


class WorkerContractTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.worker = (self.root / "worker" / "src" / "index.js").read_text(encoding="utf-8")
        self.config = (self.root / "worker" / "wrangler.toml").read_text(encoding="utf-8")

    def test_required_routes_and_controls_exist(self):
        for route in ("/health", "/v1/models", "/v1/chat/completions", "/api/chat"):
            self.assertIn(route, self.worker)
        for name in ("YASIN_WORKER_API_KEY", "YASIN_UPSTREAM_URL", "YASIN_UPSTREAM_API_KEY", "YASIN_MAX_BODY_BYTES", "YASIN_RATE_LIMIT_PER_MINUTE", "YASIN_RATE_LIMITER"):
            self.assertIn(name, self.worker)
        self.assertIn("async function rateLimit", self.worker)
        self.assertIn("rate_limiter_unavailable", self.worker)
        self.assertIn("env.YASIN_RATE_LIMITER.limit", self.worker)

    def test_worker_is_configured_for_wrangler(self):
        self.assertIn('main = "src/index.js"', self.config)
        self.assertIn('compatibility_date = "2026-09-17"', self.config)
        self.assertIn("[[ratelimits]]", self.config)
        self.assertIn('name = "YASIN_RATE_LIMITER"', self.config)

    def test_worker_does_not_expose_upstream_credential(self):
        self.assertIn("authorization", self.worker)
        self.assertIn("upstream_error", self.worker)
        self.assertNotIn("YASIN_UPSTREAM_API_KEY", self.worker.split("return json", 1)[-1].split("}", 1)[0])


if __name__ == "__main__":
    unittest.main()
