#!/usr/bin/env python3
"""Check repository layout and that no receipt contains raw text fields."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REQUIRED = ["AGENTS.md", "CLAUDE.md", "README.md", "STATE.md", "LICENSE", "NOTICE", "llms.txt",
            "benchmarks", "proposals", "reports", "contracts", "fixtures", "tests", "bin"]
FORBIDDEN_KEYS = {"prompt", "output", "content", "messages", "answer", "api_key", "authorization"}


def problems(root=ROOT):
    out = [f"missing: {p}" for p in REQUIRED if not (root / p).exists()]
    for rec in (root / "benchmarks").rglob("receipt*.json"):
        data = json.loads(rec.read_text(encoding="utf-8"))
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                bad = FORBIDDEN_KEYS & set(node)
                if bad:
                    out.append(f"raw field {sorted(bad)} in {rec.relative_to(root)}")
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return out


if __name__ == "__main__":
    p = problems()
    for line in p:
        print(line)
    print("OK" if not p else f"{len(p)} problem(s)")
    sys.exit(1 if p else 0)
