from core.documentation import render, write_generated


class DocsCommand:
    """Generate deterministic source documentation and project reports."""

    def run(self, action="all", *, base_ref="HEAD^", output=None):
        if action == "all":
            paths = write_generated(".", base_ref)
            return "\n".join(f"generated: {p}" for p in paths)
        if action not in {"api", "architecture", "report", "changes"}:
            raise ValueError("Usage: docs [all|api|architecture|report|changes] [--base REF] [--output FILE]")
        content = render(action, ".", base_ref)
        if output:
            with open(output, "w", encoding="utf-8") as handle:
                handle.write(content)
            return f"generated: {output}"
        return content.rstrip()
