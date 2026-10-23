"""Hermes pre_llm_call hook: inject the knowledge map and the memory files.

Hermes pipes a JSON payload on stdin and reads JSON on stdout; returning
{"context": "..."} appends that text to the current turn's user message.

The content lives in MEMORY_HOME (default E:\\AI\\memory\\ai-unlimited-memory), not in Hermes, so
switching harnesses means copying this file, not the data.
"""

import json
import os
import sys
from pathlib import Path

HOME = Path(os.environ.get("MEMORY_HOME", r"E:\AI\memory\ai-unlimited-memory"))
MEMORY = HOME / "memory"
INDEX = HOME / "knowledge" / "INDEX.md"

MAX_MEMORY = 3200     # chars of always-on memory (profile + projects, split below)
MAX_RULES = 3200      # chars of harness-agnostic operating rules
MAX_MAP = 3000        # chars of knowledge map
MAX_OVERLAY = 1200    # chars of the project overlay for the current cwd

HEADER = (
    "[memory] Always-on memory from the knowledge layer. The map below survived "
    "compaction; the conversation did not. If the task touches a topic, read that "
    "file before answering, and append durable findings with `kb.py append` in the "
    "same turn.\n\n"
)


def read_capped(path: Path, limit: int) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return ""
    if not text:
        return ""
    if len(text) > limit:
        text = text[:limit].rsplit("\n", 1)[0] + "\n[truncated]"
    return text


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    if payload.get("hook_event_name") not in (None, "pre_llm_call"):
        return

    parts = []
    # Rules first: the same harness-agnostic file the OpenCode plugin injects.
    rules = read_capped(MEMORY / "rules.md", MAX_RULES)
    if rules:
        parts.append(rules)
    for name, limit in (("profile.md", 1400), ("projects.md", 1800)):
        text = read_capped(MEMORY / name, limit)
        if text:
            parts.append(text)
    map_text = read_capped(INDEX, MAX_MAP)
    if map_text:
        parts.append(map_text)

    # The project overlay is scoped: it is only injected when the turn's cwd is
    # inside a registered project. kb.py owns the matching rules.
    slug = ""
    try:
        sys.path.insert(0, str(HOME))
        import kb  # noqa: E402  (same repo, imported for detect_project only)
        slug = kb.detect_project(payload.get("cwd") or os.getcwd())
    except Exception:
        slug = ""
    if slug:
        overlay = read_capped(HOME / "knowledge" / "projects" / slug / "INDEX.md", MAX_OVERLAY)
        if overlay:
            parts.append(overlay)

    if not parts:
        return
    print(json.dumps({"context": HEADER + "\n\n---\n\n".join(parts)}))


if __name__ == "__main__":
    main()
