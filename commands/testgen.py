import json

from core.test_generator import TestGenerationError, TestGenerator


class TestGenCommand:
    def run(self, action="report", root=".", changed_only=False, base_ref="HEAD^", timeout=60):
        generator = TestGenerator(root)
        if action == "report":
            return json.dumps(generator.report(changed_only, base_ref), indent=2, ensure_ascii=False)
        if action == "generate":
            return json.dumps(generator.generate(changed_only, base_ref).as_dict(), indent=2, ensure_ascii=False)
        if action == "run":
            return json.dumps(generator.run(timeout), indent=2, ensure_ascii=False)
        if action == "verify":
            report = generator.generate(changed_only, base_ref)
            if not report.supported:
                return json.dumps(report.as_dict(), indent=2, ensure_ascii=False)
            result = generator.run(timeout)
            return json.dumps({"generation": report.as_dict(), "execution": result}, indent=2, ensure_ascii=False)
        raise TestGenerationError("usage: testgen [report|generate|run|verify] [--changed] [--base REF] [--timeout SECONDS]")
