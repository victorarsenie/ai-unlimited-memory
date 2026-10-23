#!/usr/bin/env python3
"""Minimal MCP stdio server for the memory layer.

Harnesses get the knowledge base as tools instead of a shell command, so
saving a finding is one tool call and not a permission prompt.

    initialize / tools/list / tools/call   (JSON-RPC 2.0 over stdin/stdout)

Tools: kb_search, kb_append, kb_pending, kb_review, kb_rmfact, kb_stats, kb_stale,
kb_similar.
No dependencies beyond the standard library; kb.py does the work.
"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import kb  # noqa: E402  (path must be set first)

PROTOCOL = "2024-11-05"
SERVER = {"name": "ai-memory", "version": "1.0"}

TOOLS = [
    {
        "name": "kb_search",
        "description": (
            "Search every knowledge note and memory file for a term. Use before "
            "answering anything that touches past work, paths, decisions or "
            "measurements, and when the injected map does not list the topic."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Term or phrase to find."}},
            "required": ["query"],
        },
    },
    {
        "name": "kb_append",
        "description": (
            "Append a dated durable finding to an existing knowledge note. Use "
            "for measured numbers, paths, decisions and gotchas. Text should be "
            "one specific sentence, not a summary of the conversation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Note name without .md, e.g. local-llm."},
                "text": {"type": "string", "description": "The finding, one sentence."},
                "source": {
                    "type": "string",
                    "description": "Optional provenance: file path, URL, commit, or 'measured'.",
                },
            },
            "required": ["topic", "text"],
        },
    },
    {
        "name": "kb_pending",
        "description": (
            "Queue a capture candidate for review instead of writing it into a "
            "note. Use when a detail matters but you are unsure which note it "
            "belongs to, or when it has not been verified. The user promotes or "
            "clears it with kb.py review."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Candidate text, one sentence."},
                "session": {"type": "string", "description": "Optional session id for provenance."},
            },
            "required": ["text"],
        },
    },
    {
        "name": "kb_review",
        "description": (
            "List queued capture candidates, or promote one into a note "
            "(promote='N' or 'all' plus topic), or clear them all. Promoted text "
            "is appended to the note under Evidence."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "promote": {"type": "string", "description": "Candidate number or 'all'."},
                "topic": {"type": "string", "description": "Target note name."},
                "clear": {"type": "boolean", "description": "Delete all candidates."},
            },
        },
    },
    {
        "name": "kb_rmfact",
        "description": "Delete every line containing the given text. Use only when the user asks to forget something.",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "Text to match."}},
            "required": ["text"],
        },
    },
    {
        "name": "kb_stats",
        "description": "Show note count, map budget, per-note sizes and the newest write.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "kb_stale",
        "description": (
            "List notes not updated in N days (default 30) and notes whose "
            "'expires' date has passed. Use to decide whether a note still "
            "describes the machine."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"days": {"type": "integer", "description": "Age threshold in days."}},
        },
    },
    {
        "name": "kb_similar",
        "description": (
            "Rank notes by lexical similarity to a question when the map gives no "
            "obvious match. Returns note files and their answers line; open the "
            "note before answering. No model, no network."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or topic in words."},
                "top": {"type": "integer", "description": "How many notes to return (default 5)."},
                "full": {"type": "boolean", "description": "Also match the evidence tail."},
            },
            "required": ["query"],
        },
    },
]


def run(fn, *args) -> str:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            fn(*args)
    except SystemExit as exc:
        if exc.code not in (0, None):
            buf.write(f"{exc.code}\n")
    except Exception as exc:  # a tool error must not kill the server
        buf.write(f"error: {exc}\n")
    return buf.getvalue().strip() or "(no output)"


def call(name: str, args: dict) -> str:
    if name == "kb_search":
        return run(kb.cmd_search, str(args.get("query", "")))
    if name == "kb_append":
        return run(
            kb.cmd_append,
            str(args.get("topic", "")),
            str(args.get("text", "")),
            str(args.get("source", "")),
        )
    if name == "kb_pending":
        return run(kb.cmd_pending, str(args.get("text", "")), str(args.get("session", "")))
    if name == "kb_review":
        promote = args.get("promote")
        return run(
            kb.cmd_review,
            str(promote) if promote not in (None, "") else None,
            args.get("topic"),
            bool(args.get("clear", False)),
        )
    if name == "kb_rmfact":
        return run(kb.cmd_rmfact, str(args.get("text", "")))
    if name == "kb_stats":
        return run(kb.cmd_stats)
    if name == "kb_stale":
        return run(kb.cmd_stale, int(args.get("days") or 30))
    if name == "kb_similar":
        return run(
            kb.cmd_similar,
            str(args.get("query", "")),
            int(args.get("top") or 5),
            bool(args.get("full", False)),
        )
    raise ValueError(f"unknown tool: {name}")


def reply(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(msg: dict) -> None:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        reply(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": PROTOCOL,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": SERVER,
                },
            }
        )
        return
    if method == "ping":
        reply({"jsonrpc": "2.0", "id": msg_id, "result": {}})
        return
    if method == "tools/list":
        reply({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}})
        return
    if method == "tools/call":
        name = params.get("name", "")
        try:
            text = call(name, params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as exc:
            result = {"content": [{"type": "text", "text": f"error: {exc}"}], "isError": True}
        reply({"jsonrpc": "2.0", "id": msg_id, "result": result})
        return
    if msg_id is None:  # notification, nothing to answer
        return
    reply(
        {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        handle(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
