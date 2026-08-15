"""CLI for inspecting and managing persistent AI memory."""
from __future__ import annotations

import argparse

from memory import Memory


class MemoryCommand:
    def _parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="yasin-coder memory")
        sub = parser.add_subparsers(dest="action")
        save = sub.add_parser("save")
        save.add_argument("text")
        save.add_argument("--scope", default="global")
        save.add_argument("--tag", action="append", default=[])
        search = sub.add_parser("search")
        search.add_argument("query")
        search.add_argument("--scope")
        search.add_argument("--limit", type=int, default=10)
        show = sub.add_parser("list")
        show.add_argument("--scope")
        forget = sub.add_parser("forget")
        forget.add_argument("item_id", nargs="?")
        forget.add_argument("--scope")
        clear = sub.add_parser("clear")
        clear.add_argument("--scope")
        return parser

    def run(self, args=None):
        options = self._parser().parse_args(list(args or []))
        memory = Memory()
        if options.action == "save":
            item = memory.add(options.text, scope=options.scope, tags=options.tag)
            print(item["id"])
        elif options.action == "search":
            for item in memory.retrieve(options.query, scope=options.scope, limit=options.limit):
                print(f"{item['id']}\t{item['scope']}\t{item['text']}")
        elif options.action == "list":
            for item in memory.list(scope=options.scope):
                print(f"{item['id']}\t{item['scope']}\t{item['text']}")
        elif options.action == "forget":
            print(f"Removed: {memory.forget(options.item_id, scope=options.scope)}")
        elif options.action == "clear":
            print(f"Removed: {memory.clear(scope=options.scope)}")
        else:
            self._parser().print_help()
