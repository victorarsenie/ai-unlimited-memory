#!/usr/bin/env python3
"""kb - the knowledge layer for the personal memory system.

Files are canonical. The map (knowledge/INDEX.md) is generated from the notes'
front matter, capped so it stays cheap enough to inject every turn.

    python kb.py index            rebuild knowledge/INDEX.md
    python kb.py lint             check structure and the map
    python kb.py stats            sizes and budget
    python kb.py dupes            repeated evidence lines
    python kb.py project          overlay for the current directory
    python kb.py project <path>   overlay for a given directory
    python kb.py search <term>    grep notes and memory
    python kb.py show <topic>     print a note
    python kb.py append <topic> <text>   add a dated finding under Evidence
    python kb.py append <topic> <text> --source <ref> [--force]
    python kb.py owner <topic> <human|agent>   who may write the note
    python kb.py stale [--days N]        notes not touched, and expired ones
    python kb.py similar <query>         BM25 recall over the notes (no process)
    python kb.py embed [--status|--start|--stop|--keep]   optional embedding helper
    python kb.py rmfact <text>    delete lines containing text (fact-level delete)
    python kb.py pending <text>   queue a capture candidate for review
    python kb.py review           list candidates
    python kb.py review --promote <n> --topic <topic>
    python kb.py review --clear
    python kb.py consolidate      propose near-duplicate merges
    python kb.py consolidate --apply
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KB = ROOT / "knowledge"
MEM = ROOT / "memory"
PENDING = KB / "pending"
PROJECTS = KB / "projects"
INDEX = KB / "INDEX.md"
MAX_MAP = 3000          # characters, injected every turn
MAX_PROJECT_MAP = 1200  # characters per project overlay, injected only in that repo
MAX_NOTE_LINES = 400    # a note bigger than this is a document, split it
MAX_PENDING_CHARS = 800  # one candidate, not a transcript

# Embeddings are optional: `kb.py similar` blends them with the lexical score
# when the server answers, and falls back to lexical alone when it does not.
# The model is 942 MB resident, so it is started on demand and stopped again
# unless `--keep` was asked for (RAM here is spoken for by Strata's experts).
EMBED_BASE = os.environ.get("KB_EMBED_BASE", "http://127.0.0.1:8090")
EMBED_MODEL = Path(os.environ.get(
    "KB_EMBED_MODEL", r"E:\AI\models\gguf\embeddinggemma-300M-Q8_0.gguf"))
EMBED_SERVER = Path(os.environ.get(
    "KB_EMBED_SERVER", r"E:\AI\engines\llama\llama-b11738-cuda13\llama-server.exe"))
EMBED_CACHE = KB / ".index" / "embeddings.json"
EMBED_PID = KB / ".index" / "embed.pid"
EMBED_DIM = 768
EMBED_BLEND = 0.75      # share of the embedding score; the rest is normalised lexical
EMBED_MIN_FREE_MB = 4096  # never start the embedder below this much free physical RAM

FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_front_matter(text: str) -> tuple[dict, str]:
    m = FM.match(text)
    if not m:
        return {}, text
    meta: dict[str, object] = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value
    return meta, text[m.end():]


def notes_in(folder: Path) -> list[dict]:
    out = []
    for p in sorted(folder.glob("*.md")):
        if p.name.lower() in ("index.md", "_domain.md"):
            continue
        raw = p.read_text(encoding="utf-8-sig")
        meta, body = parse_front_matter(raw)
        h1 = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), p.stem)
        out.append({
            "path": p,
            "file": p.name,
            "label": str(p.relative_to(KB)).replace("\\", "/"),
            "title": str(meta.get("title") or h1),
            "answers": str(meta.get("answers") or "").strip(),
            "updated": str(meta.get("updated") or ""),
            "expires": str(meta.get("expires") or ""),
            "owner": str(meta.get("owner") or "agent").strip().lower(),
            "tags": meta.get("tags") or [],
            "lines": len(body.splitlines()),
            "has_fm": bool(meta),
        })
    return out


def notes() -> list[dict]:
    return notes_in(KB)


DOMAIN_SKIP = {"pending", "_archive", ".index"}
MAX_DOMAIN_MAP = 1600   # characters per domain map, read on demand


def domain_dirs() -> list[Path]:
    if not KB.is_dir():
        return []
    return [d for d in sorted(KB.iterdir())
            if d.is_dir() and d.name not in DOMAIN_SKIP and (d / "_domain.md").is_file()]


def domain_meta(folder: Path) -> dict:
    meta, _ = parse_front_matter((folder / "_domain.md").read_text(encoding="utf-8-sig"))
    return {
        "name": folder.name,
        "title": str(meta.get("title") or folder.name),
        "answers": str(meta.get("answers") or ""),
        "updated": str(meta.get("updated") or ""),
    }


def domain_items(folder: Path) -> list[dict]:
    """Notes in a domain. `projects` is one level deeper: one entry per project."""
    if folder.name != "projects":
        return notes_in(folder)
    out = []
    for sub in sorted(folder.iterdir()):
        if not (sub.is_dir() and (sub / "project.md").is_file()):
            continue
        meta, body = parse_front_matter((sub / "project.md").read_text(encoding="utf-8-sig"))
        h1 = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), sub.name)
        out.append({
            "path": sub / "project.md",
            "file": f"{sub.name}/INDEX.md",
            "label": f"projects/{sub.name}",
            "title": str(meta.get("title") or h1),
            "answers": str(meta.get("answers") or "").strip(),
            "updated": str(meta.get("updated") or ""),
            "expires": "",
            "owner": "agent",
            "tags": meta.get("tags") or [],
            "lines": 0,
            "has_fm": bool(meta),
        })
    return out


def build_map(items: list[dict], limit: int = MAX_MAP, title: str = "Knowledge map") -> str:
    def row(n):
        tags = " ".join(n["tags"]) if isinstance(n["tags"], list) else str(n["tags"])
        return f"| {n['title']} | {n['file']} | {n['answers'] or 'n/a'} | {tags} |"

    header = (
        f"# {title}\n\n"
        "Generated by `kb.py index` - do not edit by hand. Open the note before answering;\n"
        "append durable findings with `kb.py append <topic> \"...\"` in the same turn.\n\n"
        "| topic | file | answers | tags |\n|---|---|---|---|\n"
    )
    rows = [row(n) for n in sorted(items, key=lambda n: n["title"].lower())]
    recent = sorted(
        [n for n in items if n["updated"]],
        key=lambda n: n["updated"], reverse=True,
    )[:5]
    footer = "\n## Recently updated\n" + "".join(
        f"- {n['updated']} - {n['title']}\n" for n in recent
    ) if recent else ""

    # trim from the oldest rows until the map fits
    hidden = 0
    while rows and len(header) + sum(len(r) + 1 for r in rows) + len(footer) > limit:
        oldest = min(items, key=lambda n: n["updated"] or "0000")
        rows = [r for r in rows if not r.startswith(f"| {oldest['title']} |")]
        items = [n for n in items if n is not oldest]
        hidden += 1

    text = header + "\n".join(rows) + footer
    if hidden:
        text += f"\n\n[{hidden} topic(s) hidden to stay under {limit} chars - merge or archive notes]\n"
    return text


def project_dirs() -> list[Path]:
    if not PROJECTS.is_dir():
        return []
    return [d for d in sorted(PROJECTS.iterdir())
            if d.is_dir() and (d / "project.md").is_file()]


def _as_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)] if str(value or "").strip() else []


def project_meta(folder: Path) -> dict:
    meta, _ = parse_front_matter((folder / "project.md").read_text(encoding="utf-8-sig"))
    return {
        "slug": folder.name,
        "dir": folder,
        "title": str(meta.get("title") or folder.name),
        "answers": str(meta.get("answers") or ""),
        "updated": str(meta.get("updated") or ""),
        "remotes": _as_list(meta.get("remotes")),
        "paths": _as_list(meta.get("paths")),
    }


def project_notes(folder: Path) -> list[dict]:
    out = []
    for p in sorted(folder.glob("*.md")):
        if p.name == "INDEX.md":
            continue
        raw = p.read_text(encoding="utf-8-sig")
        meta, body = parse_front_matter(raw)
        h1 = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), p.stem)
        out.append({
            "path": p,
            "file": p.name,
            "title": str(meta.get("title") or h1),
            "answers": str(meta.get("answers") or "").strip(),
            "updated": str(meta.get("updated") or ""),
            "expires": str(meta.get("expires") or ""),
            "owner": str(meta.get("owner") or "agent").strip().lower(),
            "tags": meta.get("tags") or [],
            "lines": len(body.splitlines()),
            "has_fm": bool(meta),
        })
    return out


def _norm_path(value: str) -> str:
    return str(value).replace("\\", "/").rstrip("/").lower()


def git_remote(cwd: str) -> str:
    try:
        import subprocess
        res = subprocess.run(
            ["git", "-C", cwd, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=5,
        )
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        return ""


def detect_project(cwd: str | None = None) -> str:
    """Longest matching `paths:` entry wins; otherwise match the git origin URL."""
    here = _norm_path(cwd or str(Path.cwd()))
    best: tuple[int, str] | None = None
    metas = [project_meta(d) for d in project_dirs()]
    for meta in metas:
        for path in meta["paths"]:
            np = _norm_path(path)
            if np and (here == np or here.startswith(np + "/")):
                if best is None or len(np) > best[0]:
                    best = (len(np), meta["slug"])
    if best:
        return best[1]
    url = _norm_path(git_remote(cwd or str(Path.cwd()))).removesuffix(".git")
    if url:
        for meta in metas:
            for remote in meta["remotes"]:
                nr = _norm_path(remote).removesuffix(".git")
                if nr and (nr in url or url in nr):
                    return meta["slug"]
    return ""


def build_domain_map(rows: list[tuple[dict, int]], root_notes: list[dict],
                     all_notes: list[dict]) -> str:
    header = (
        "# Knowledge map\n\n"
        "Generated by `kb.py index` - do not edit by hand. One row per domain: open\n"
        "`knowledge/<domain>/INDEX.md` for its notes, then the note itself. Append with\n"
        "`kb.py append <domain>/<note> \"...\"` in the same turn.\n\n"
        "| domain | map | answers | notes |\n|---|---|---|---|\n"
    )
    body = "".join(
        f"| {m['title']} | {m['name']}/INDEX.md | {m['answers'] or 'n/a'} | {count} |\n"
        for m, count in rows
    )
    text = header + body
    if root_notes:
        text += "\n## At the root\n" + "".join(
            f"- {n['file']} - {n['answers'] or n['title']}\n" for n in root_notes
        )
    recent = sorted([n for n in all_notes if n["updated"]],
                    key=lambda n: n["updated"], reverse=True)[:5]
    footer = "\n## Recently updated\n" + "".join(
        f"- {n['updated']} - {n['label']}\n" for n in recent
    ) if recent else ""
    if len(text) + len(footer) <= MAX_MAP:
        text += footer
    return text


def cmd_index() -> int:
    over = False
    rows: list[tuple[dict, int]] = []
    for folder in domain_dirs():
        meta = domain_meta(folder)
        items = domain_items(folder)
        dmap = build_map(items, MAX_DOMAIN_MAP, meta["title"])
        (folder / "INDEX.md").write_text(dmap, encoding="utf-8")
        rows.append((meta, len(items)))
        cap = "" if len(dmap) <= MAX_DOMAIN_MAP else "  OVER CAP"
        over = over or bool(cap)
        print(f"  domain {meta['name']}: {len(dmap)} chars, {len(items)} note(s){cap}")
    for folder in project_dirs():
        meta = project_meta(folder)
        pmap = build_map(project_notes(folder), MAX_PROJECT_MAP, f"Project overlay: {meta['title']}")
        (folder / "INDEX.md").write_text(pmap, encoding="utf-8")
        cap = "" if len(pmap) <= MAX_PROJECT_MAP else "  OVER CAP"
        over = over or bool(cap)
        print(f"  project {meta['slug']}: {len(pmap)} chars{cap}")
    text = build_domain_map(rows, notes(), _all_notes())
    INDEX.write_text(text, encoding="utf-8")
    over = over or len(text) > MAX_MAP
    print(f"index: {len(text)} chars, {len(rows)} domain(s), {len(_all_notes())} note(s)"
          + ("  OVER CAP" if over else ""))
    return 1 if over else 0


def cmd_lint() -> int:
    problems = []
    map_text = INDEX.read_text(encoding="utf-8-sig") if INDEX.is_file() else ""

    # Root notes (user rules) must be structured; they are listed under "At the root".
    for n in notes():
        if not n["has_fm"]:
            problems.append(f"{n['file']}: no front matter")
        if not n["answers"]:
            problems.append(f"{n['file']}: no 'answers' line")
        if n["lines"] > MAX_NOTE_LINES:
            problems.append(f"{n['file']}: {n['lines']} lines (> {MAX_NOTE_LINES}) - split")

    # Every domain: a _domain.md with answers, a current INDEX, structured notes.
    for folder in domain_dirs():
        meta = domain_meta(folder)
        if not meta["answers"]:
            problems.append(f"{meta['name']}/_domain.md: no 'answers' line")
        dmap_path = folder / "INDEX.md"
        if not dmap_path.is_file():
            problems.append(f"{meta['name']}/INDEX.md: missing - run index")
            continue
        dmap = dmap_path.read_text(encoding="utf-8-sig")
        if len(dmap) > MAX_DOMAIN_MAP:
            problems.append(f"{meta['name']}/INDEX.md: {len(dmap)} chars (> {MAX_DOMAIN_MAP})")
        listed = set(re.findall(r"\| ([^|]+\.md) \|", dmap))
        items = domain_items(folder)
        for n in items:
            if not n["has_fm"]:
                problems.append(f"{n['label']}: no front matter")
            if not n["answers"]:
                problems.append(f"{n['label']}: no 'answers' line")
            if n["file"] not in listed:
                problems.append(f"{n['label']}: not on the domain map - run index")
        for orphan in listed - {n["file"] for n in items}:
            problems.append(f"{meta['name']}/{orphan}: on the map but the file is gone")
        if f"| {meta['name']}/INDEX.md |" not in map_text:
            problems.append(f"{meta['name']}: missing from the global map - run index")

    if len(map_text) > MAX_MAP:
        problems.append(f"INDEX.md: {len(map_text)} chars (> {MAX_MAP})")
    for n in _all_notes() + [{"path": p, "label": p.name} for p in sorted(MEM.glob("*.md"))]:
        raw = n["path"].read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            problems.append(f"{n['label']}: UTF-8 BOM - strip it (adapters need plain utf-8)")
    for n in _all_notes():
        if n["expires"]:
            age = _age_days(n["expires"])
            if age is not None and age >= 0:
                problems.append(f"{n['label']}: expired {n['expires']} - re-verify or delete")

    for folder in project_dirs():
        meta = project_meta(folder)
        if not meta["paths"] and not meta["remotes"]:
            problems.append(f"projects/{meta['slug']}: no paths or remotes - cannot be detected")
        for n in project_notes(folder):
            if not n["has_fm"]:
                problems.append(f"projects/{meta['slug']}/{n['file']}: no front matter")
            if not n["answers"]:
                problems.append(f"projects/{meta['slug']}/{n['file']}: no 'answers' line")
        pmap = folder / "INDEX.md"
        if not pmap.is_file():
            problems.append(f"projects/{meta['slug']}/INDEX.md: missing - run index")
        elif len(pmap.read_text(encoding="utf-8-sig")) > MAX_PROJECT_MAP:
            problems.append(f"projects/{meta['slug']}/INDEX.md: over {MAX_PROJECT_MAP} chars")

    if not problems:
        protected = sum(1 for n in _all_notes() if n["owner"] == "human")
        extra = f", {protected} owner: human" if protected else ""
        print(f"lint: ok ({len(domain_dirs())} domains, {len(_all_notes())} notes, "
              f"map {len(map_text)} chars{extra})")
        return 0
    print(f"lint: {len(problems)} problem(s)")
    for p in problems:
        print("  - " + p)
    return 1


def cmd_project(where: str | None = None) -> int:
    metas = [project_meta(d) for d in project_dirs()]
    if where:
        slug = detect_project(where)
        if not slug:
            print(f"project: no overlay matches {where}")
            return 1
        print(slug)
        return 0
    if not metas:
        print("project: none defined (create knowledge/projects/<slug>/project.md)")
        return 0
    here = detect_project()
    for m in metas:
        mark = " *" if m["slug"] == here else ""
        print(f"{m['slug']}{mark}  {m['title']}")
        if m["paths"]:
            print("   paths:   " + ", ".join(m["paths"]))
        if m["remotes"]:
            print("   remotes: " + ", ".join(m["remotes"]))
    if here:
        print(f"\ncwd matches: {here}")
    return 0


def iter_text():
    for p in text_files():
        for i, line in enumerate(p.read_text(encoding="utf-8-sig").splitlines(), 1):
            yield p, i, line


def cmd_search(term: str) -> int:
    needle = term.lower()
    hits = 0
    for p, i, line in iter_text():
        if needle in line.lower():
            print(f"{p.relative_to(ROOT)}:{i}: {line.strip()[:160]}")
            hits += 1
    print(f"-- {hits} hit(s)")
    return 0 if hits else 1


def pending_file(day: str | None = None) -> Path:
    PENDING.mkdir(parents=True, exist_ok=True)
    return PENDING / f"{(day or date.today().isoformat())}.md"


def note_path(topic: str) -> Path:
    topic = topic if topic.endswith(".md") else topic + ".md"
    p = KB / topic
    if not p.is_file():
        raise SystemExit(f"no such note: {p.name} (create it first)")
    return p


def note_owner(path: Path) -> str:
    """`owner: human` means the user wrote it; agents need an explicit ask first."""
    meta, _ = parse_front_matter(path.read_text(encoding="utf-8-sig"))
    return str(meta.get("owner") or "agent").strip().lower()


def write_blocked(path: Path, force: bool, action: str) -> bool:
    if force or note_owner(path) != "human":
        return False
    print(f"{action}: {path.name} is owner: human - ask the user first, "
          "then rerun with --force after the edit is approved")
    return True


def cmd_owner(topic: str, value: str) -> int:
    value = value.strip().lower()
    if value not in ("human", "agent"):
        print("owner: value must be 'human' or 'agent'")
        return 2
    p = note_path(topic)
    raw = p.read_text(encoding="utf-8-sig")
    meta, body = parse_front_matter(raw)
    if not meta:
        print(f"owner: {p.name} has no front matter")
        return 2
    meta["owner"] = value
    fm = "---\n" + "\n".join(
        f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}"
        for k, v in meta.items()
    ) + "\n---\n"
    p.write_text(fm + body, encoding="utf-8")
    print(f"owner: {p.name} -> {value}")
    return cmd_index()


def cmd_show(topic: str) -> int:
    print(note_path(topic).read_text(encoding="utf-8-sig"))
    return 0


def cmd_append(topic: str, text: str, source: str = "", force: bool = False) -> int:
    p = note_path(topic)
    if write_blocked(p, force, "append"):
        return 3
    raw = p.read_text(encoding="utf-8-sig")
    meta, body = parse_front_matter(raw)
    stamp = date.today().isoformat()
    line = text.strip()
    if source.strip():
        line += f" (source: {source.strip()})"
    entry = f"- {stamp}: {line}\n"

    if "## Evidence" not in body:
        body = body.rstrip() + "\n\n## Evidence\n\n"
    head, _, tail = body.partition("## Evidence")
    tail_lines = tail.splitlines(keepends=True)
    body = head + "## Evidence" + "".join(tail_lines).rstrip("\n") + "\n" + entry

    if meta:
        meta["updated"] = stamp
        fm = "---\n" + "\n".join(
            f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}"
            for k, v in meta.items()
        ) + "\n---\n"
        raw = fm + body
    else:
        raw = body
    p.write_text(raw, encoding="utf-8")
    print(f"appended to {p.name}")
    return cmd_index()


def cmd_rmfact(text: str, force: bool = False) -> int:
    needle = text.lower()
    removed = 0
    skipped = 0
    for p in text_files():
        if not force and note_owner(p) == "human":
            skipped += 1
            continue
        lines = p.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        keep = [ln for ln in lines if needle not in ln.lower()]
        if len(keep) != len(lines):
            removed += len(lines) - len(keep)
            p.write_text("".join(keep), encoding="utf-8")
            print(f"{p.name}: removed {len(lines) - len(keep)} line(s)")
    if skipped:
        print(f"-- {skipped} owner: human note(s) skipped (rerun with --force if approved)")
    print(f"-- {removed} line(s) removed")
    return cmd_index()


def cmd_pending(text: str, session: str = "") -> int:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        print("pending: empty text")
        return 2
    if len(text) > MAX_PENDING_CHARS:
        text = text[:MAX_PENDING_CHARS].rsplit(" ", 1)[0] + " ..."
    p = pending_file()
    digest = hashlib.sha1(text.lower().encode("utf-8")).hexdigest()[:12]
    existing = p.read_text(encoding="utf-8-sig") if p.is_file() else ""
    if digest in existing:
        print("pending: duplicate, ignored")
        return 0
    stamp = datetime.now().strftime("%H:%M:%S")
    who = f"session={session} " if session else ""
    line = f"- {stamp} {who}id={digest} {text}\n"
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)
    print(f"pending: queued in {p.name} ({len(text)} chars)")
    return 0


def _pending_entries() -> list[dict]:
    out = []
    if not PENDING.is_dir():
        return out
    for p in sorted(PENDING.glob("*.md")):
        for raw in p.read_text(encoding="utf-8-sig").splitlines():
            if not raw.strip().startswith("- "):
                continue
            body = re.sub(r"^- \d{2}:\d{2}:\d{2}\s+", "", raw.strip())
            body = re.sub(r"^session=\S+\s+", "", body)
            body = re.sub(r"^id=[0-9a-f]{12}\s+", "", body)
            out.append({"file": p, "raw": raw, "text": body})
    return out


def cmd_review(promote: str | None = None, topic: str | None = None, clear: bool = False) -> int:
    entries = _pending_entries()
    if clear:
        for p in sorted(PENDING.glob("*.md")):
            p.unlink()
        print(f"review: cleared {len(entries)} candidate(s)")
        return 0
    if promote:
        if not topic:
            print("review: --promote needs --topic <note>")
            return 2
        if promote == "all":
            chosen = entries
        else:
            try:
                idx = int(promote)
            except ValueError:
                print("review: --promote takes a number or 'all'")
                return 2
            if not 1 <= idx <= len(entries):
                print(f"review: no candidate {idx} (have {len(entries)})")
                return 2
            chosen = [entries[idx - 1]]
        for e in chosen:
            cmd_append(topic, e["text"])
        names = {e["file"] for e in chosen}
        for p in names:
            drop = [e["raw"] for e in chosen if e["file"] == p]
            lines = p.read_text(encoding="utf-8-sig").splitlines(keepends=True)
            kept = [ln for ln in lines if ln.rstrip("\n") not in drop]
            if kept:
                p.write_text("".join(kept), encoding="utf-8", newline="\n")
            else:
                p.unlink()
        print(f"review: promoted {len(chosen)} candidate(s) to {topic}")
        return 0
    if not entries:
        print("review: no pending candidates")
        return 0
    print(f"review: {len(entries)} candidate(s) in {PENDING.relative_to(ROOT)}")
    for i, e in enumerate(entries, 1):
        print(f"  [{i}] {e['file'].stem}  {e['text'][:160]}")
    print("promote with: kb.py review --promote N --topic <note>   (or --clear)")
    return 0


def _norm_tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cmd_consolidate(apply: bool = False) -> int:
    """Cluster evidence lines that say nearly the same thing; keep the fullest."""
    items = []
    skipped = 0
    for p in sorted(KB.glob("*.md")):
        if p.name == "INDEX.md":
            continue
        if note_owner(p) == "human":
            skipped += 1
            continue
        for raw in p.read_text(encoding="utf-8-sig").splitlines():
            if not raw.strip().startswith("- "):
                continue
            body = re.sub(r"^- \d{4}-\d{2}-\d{2}:\s*", "", raw.strip())
            tokens = _norm_tokens(body)
            if len(tokens) < 6:
                continue
            items.append({"file": p, "raw": raw.rstrip("\n"), "text": body, "tokens": tokens})

    clusters: list[dict] = []
    for it in items:
        for c in clusters:
            if _jaccard(it["tokens"], c["rep"]) >= 0.85:
                c["items"].append(it)
                break
        else:
            clusters.append({"rep": it["tokens"], "items": [it]})

    groups = [c for c in clusters if len(c["items"]) > 1]
    if not groups:
        print("consolidate: no near-duplicates"
              + (f" ({skipped} owner: human note(s) untouched)" if skipped else ""))
        return 0

    print(f"consolidate: {len(groups)} cluster(s)")
    remove: dict[Path, list[str]] = {}
    for c in groups:
        keeper = max(c["items"], key=lambda x: (len(x["text"]), x["raw"]))
        print(f"  keep  {keeper['file'].name}: {keeper['text'][:130]}")
        for it in c["items"]:
            if it is keeper:
                continue
            print(f"  drop  {it['file'].name}: {it['text'][:130]}")
            remove.setdefault(it["file"], []).append(it["raw"])

    if not apply:
        print("-- dry run; rerun with --apply to drop the redundant lines")
        return 0

    for p, raws in remove.items():
        lines = p.read_text(encoding="utf-8-sig").splitlines(keepends=True)
        pending = list(raws)
        kept = []
        for ln in lines:
            key = ln.rstrip("\n")
            if key in pending:
                pending.remove(key)
                continue
            kept.append(ln)
        p.write_text("".join(kept), encoding="utf-8", newline="\n")
    print(f"consolidate: removed {sum(len(v) for v in remove.values())} line(s)")
    return cmd_index()


def _age_days(stamp: str) -> int | None:
    try:
        return (date.today() - date.fromisoformat(stamp[:10])).days
    except ValueError:
        return None


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "are", "was",
    "were", "not", "but", "its", "has", "have", "had", "you", "your", "our",
    "out", "all", "can", "will", "when", "what", "which", "who", "how", "why",
    "than", "then", "them", "they", "there", "their", "about", "over", "under",
    "after", "before", "also", "only", "more", "most", "less", "very", "use",
    "used", "using", "one", "two", "three", "four", "five", "any", "each",
    "does", "did", "why", "get", "got", "make", "made", "still",
}


def _tokens(text: str) -> list[str]:
    out = []
    for raw in re.findall(r"[a-z0-9]+", text.lower()):
        if len(raw) < 3 or raw in STOPWORDS:
            continue
        if len(raw) > 4 and raw.endswith("s") and not raw.endswith("ss"):
            raw = raw[:-1]
        out.append(raw)
    return out


def _answer_text(path: Path) -> str:
    """Everything above the first `## ` heading: the Answer block, not the evidence tail."""
    raw = path.read_text(encoding="utf-8-sig")
    _, body = parse_front_matter(raw)
    keep = []
    for line in body.splitlines():
        if line.startswith("## "):
            break
        keep.append(line)
    return " ".join(keep)


def _vector(tokens: list[str], idf: dict[str, float], default_idf: float = 1.0) -> dict[str, float]:
    tf: dict[str, int] = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    vec = {}
    for token, count in tf.items():
        weight = (1 + math.log(count)) * idf.get(token, default_idf)
        if weight:
            vec[token] = weight
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


def _embed_port() -> str:
    try:
        return str(int(EMBED_BASE.rsplit(":", 1)[1].rstrip("/")))
    except (IndexError, ValueError):
        return "8090"


def _embed_health(timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(EMBED_BASE + "/health", timeout=timeout) as r:
            return json.load(r).get("status") == "ok"
    except Exception:
        return False


def _embed_post(texts: list[str]) -> list[list[float]]:
    payload = json.dumps({"input": texts, "model": EMBED_MODEL.name}).encode()
    req = urllib.request.Request(
        EMBED_BASE + "/v1/embeddings", data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    rows = sorted(data["data"], key=lambda d: d.get("index", 0))
    return [row["embedding"] for row in rows]


def _free_ram_mb() -> int:
    """Physical RAM available right now, in MB (0 when it cannot be read)."""
    if os.name != "nt":
        return 0
    try:
        import ctypes

        class MEMSTATUS(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMSTATUS()
        stat.dwLength = ctypes.sizeof(MEMSTATUS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return int(stat.ullAvailPhys / (1024 * 1024))
    except Exception:
        return 0


def _embed_start(wait: float = 40.0) -> bool:
    if _embed_health():
        return False
    if not EMBED_MODEL.is_file():
        print(f"embed: model not found: {EMBED_MODEL}")
        return False
    if not EMBED_SERVER.is_file():
        print(f"embed: llama-server not found: {EMBED_SERVER}")
        return False
    free = _free_ram_mb()
    if free and free < EMBED_MIN_FREE_MB:
        print(f"embed: refused, only {free} MB free RAM (needs {EMBED_MIN_FREE_MB} MB "
              "- Strata's experts would be evicted); using lexical")
        return False
    flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [str(EMBED_SERVER), "-m", str(EMBED_MODEL), "--embeddings",
         "-c", "512", "--port", _embed_port(), "--host", "127.0.0.1", "--no-webui"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    EMBED_PID.parent.mkdir(parents=True, exist_ok=True)
    EMBED_PID.write_text(str(proc.pid), encoding="utf-8")
    deadline = time.time() + wait
    while time.time() < deadline:
        if _embed_health(1.0):
            return True
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    print("embed: server did not become healthy")
    return False


def _embed_stop() -> bool:
    """Stop only the server this script started, never the main inference engine."""
    if not EMBED_PID.is_file():
        return False
    try:
        pid = int(EMBED_PID.read_text(encoding="utf-8-sig").strip())
    except ValueError:
        EMBED_PID.unlink(missing_ok=True)
        return False
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, 15)
    except Exception:
        pass
    EMBED_PID.unlink(missing_ok=True)
    return True


def _cos(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _doc_text(n: dict) -> str:
    tags = n["tags"] if isinstance(n["tags"], list) else [str(n["tags"])]
    return f"title: {n['title']} | text: {n['answers']}. {_answer_text(n['path'])} {' '.join(tags)}"


def _load_cache() -> dict:
    try:
        data = json.loads(EMBED_CACHE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"model": EMBED_MODEL.name, "dim": EMBED_DIM, "docs": {}}
    if data.get("model") != EMBED_MODEL.name or data.get("dim") != EMBED_DIM:
        return {"model": EMBED_MODEL.name, "dim": EMBED_DIM, "docs": {}}
    return data


def _save_cache(data: dict) -> None:
    EMBED_CACHE.parent.mkdir(parents=True, exist_ok=True)
    EMBED_CACHE.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def _vectors(items: list[dict]) -> dict[str, list[float]]:
    """Embedding per note, re-embedding only the notes whose text changed."""
    cache = _load_cache()
    docs = cache["docs"]
    dirty = []
    for n in items:
        text = _doc_text(n)
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        row = docs.get(n["label"])
        if not row or row.get("hash") != digest:
            dirty.append((n, text, digest))
    if dirty:
        batch = 32
        for start in range(0, len(dirty), batch):
            chunk = dirty[start:start + batch]
            for (n, _, digest), vec in zip(chunk, _embed_post([t for _, t, _ in chunk])):
                docs[n["label"]] = {"hash": digest, "vec": [round(v, 5) for v in vec]}
        _save_cache(cache)
    labels = {n["label"] for n in items}
    for stale in [k for k in docs if k not in labels]:
        docs.pop(stale, None)
    _save_cache(cache)
    return {n["label"]: docs[n["label"]]["vec"] for n in items if n["label"] in docs}


def _lexical_scores(items: list[dict], query: str, full: bool) -> list[tuple[float, dict]]:
    """BM25 over the notes: no model, no process, no index on disk.

    Length normalisation is the point: without it the 26 KB local-llm note wins
    every query simply by containing more words.
    """
    docs = []
    for n in items:
        tags = n["tags"] if isinstance(n["tags"], list) else [str(n["tags"])]
        text = " ".join([n["title"], n["answers"], _answer_text(n["path"]), " ".join(tags)])
        if full:
            text += " " + n["path"].read_text(encoding="utf-8-sig")
        docs.append((n, _tokens(text)))
    if not docs:
        return []
    total = len(docs)
    avgdl = sum(len(toks) for _, toks in docs) / total or 1.0
    df: dict[str, int] = {}
    for _, toks in docs:
        for token in set(toks):
            df[token] = df.get(token, 0) + 1
    terms = _tokens(query)
    if not terms:
        return []
    k1, b = 1.2, 0.75
    out = []
    for n, toks in docs:
        tf: dict[str, int] = {}
        for token in toks:
            tf[token] = tf.get(token, 0) + 1
        dl = len(toks) or 1
        score = 0.0
        for term in terms:
            f = tf.get(term)
            if not f:
                continue
            idf = math.log(1 + (total - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * dl / avgdl))
        out.append((score / len(terms), n))
    return out


def cmd_similar(query: str, top: int = 5, full: bool = True,
                embed_mode: str = "auto", keep: bool = False) -> int:
    """Rank notes by meaning if an embedder is already running, else by words.

    Nothing is spawned from here: the lexical path needs no process, and a
    separate embedder costs ~940 MB resident, which this machine cannot spare
    while Strata's experts are pinned. `kb.py embed --start` is the manual opt-in.

    Embeddings, when present, are blended with the lexical score: vectors handle
    paraphrase, tokens keep paths, versions and identifiers exact.
    """
    items = _all_notes()
    if not items:
        print("similar: no notes")
        return 1
    lex = _lexical_scores(items, query, full)
    lexical_only = lex or [(0.0, n) for n in items]
    top_lex = max((s for s, _ in lexical_only), default=0.0) or 1.0
    lex_norm = {n["label"]: s / top_lex for s, n in lexical_only}

    vectors = None
    mode = "lexical"
    if embed_mode != "off" and EMBED_MODEL.is_file() and EMBED_SERVER.is_file() and _embed_health():
        try:
            vectors = _vectors(items)
            qv = _embed_post([f"task: search result | query: {query}"])[0]
            mode = "embeddings" if not lex else "blended"
        except Exception as exc:
            print(f"similar: embedder failed ({exc}); using lexical")
            vectors = None

    if not lex and not vectors:
        print("similar: the query has no usable words")
        return 2

    scored = []
    for n in items:
        label = n["label"]
        score = lex_norm.get(label, 0.0)
        if vectors and label in vectors:
            score = EMBED_BLEND * _cos(qv, vectors[label]) + (1 - EMBED_BLEND) * score
        scored.append((score, n))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["label"]))
    hits = [(s, n) for s, n in scored if s > 0.02][:top]
    if not hits:
        if not full:
            print("similar: no answer-block match, searching full text")
            return cmd_similar(query, top, True, embed, keep)
        print(f"similar: nothing matches '{query}'")
        return 1
    print(f"similar: {len(hits)} of {len(items)} notes for '{query}' ({mode}"
          + (", full text" if full else "") + ")")
    if mode == "lexical" and embed_mode == "auto" and EMBED_MODEL.is_file():
        print("  hint: lexical only (no helper process); semantic recall needs `kb.py embed --start`")
    for score, n in hits:
        print(f"  {score:.2f}  {n['label']:<30} {n['answers'][:70]}")
    return 0


def cmd_embed(action: str = "rebuild", keep: bool = False) -> int:
    if action == "status":
        running = _embed_health()
        cache = _load_cache()
        print(f"server   {'up at ' + EMBED_BASE if running else 'down'}")
        state = "present" if EMBED_MODEL.is_file() else "MISSING"
        print(f"model    {EMBED_MODEL.name} {state}")
        print(f"cache    {len(cache['docs'])} note(s), dim {cache['dim']}")
        print(f"paths    model={EMBED_MODEL}")
        print(f"         cache={EMBED_CACHE}")
        return 0 if EMBED_MODEL.is_file() else 1
    if action == "stop":
        print("embed: stopped" if _embed_stop() else "embed: nothing to stop")
        return 0
    started = False
    if not _embed_health():
        started = _embed_start()
    if not _embed_health():
        print("embed: server unavailable")
        return 1
    if action == "start":
        print(f"embed: running at {EMBED_BASE}")
        return 0
    items = _all_notes()
    vectors = _vectors(items)
    if started and not keep:
        _embed_stop()
    if not vectors:
        print("embed: no notes to index")
        return 1
    print(f"embed: {len(vectors)} note(s) cached, dim {len(next(iter(vectors.values())))}")
    return 0


def _all_notes() -> list[dict]:
    out = [dict(n, label=n["file"]) for n in notes()]
    for folder in domain_dirs():
        if folder.name == "projects":
            for sub in sorted(folder.iterdir()):
                if sub.is_dir():
                    out += [dict(n, label=f"projects/{sub.name}/{n['file']}")
                            for n in notes_in(sub)]
        else:
            out += [dict(n, label=f"{folder.name}/{n['file']}") for n in notes_in(folder)]
    return out


def text_files() -> list[Path]:
    """Every note and memory file, in the order search/rmfact should walk them."""
    out = [p for p in sorted(KB.glob("*.md")) if p.name != "INDEX.md"]
    out += [p for p in sorted(MEM.glob("*.md"))]
    for folder in domain_dirs():
        if folder.name == "projects":
            for sub in sorted(folder.iterdir()):
                if sub.is_dir():
                    out += [p for p in sorted(sub.glob("*.md")) if p.name != "INDEX.md"]
        else:
            out += [p for p in sorted(folder.glob("*.md")) if p.name != "INDEX.md"]
    return out


def cmd_stale(days: int = 30) -> int:
    """Notes that have not been touched, and notes that carry a passed expires date."""
    expired, stale, unknown = [], [], []
    for n in _all_notes():
        if n["expires"]:
            age = _age_days(n["expires"])
            if age is not None and age >= 0:
                expired.append(n)
        age = _age_days(n["updated"]) if n["updated"] else None
        if age is None:
            unknown.append(n)
        elif age >= days:
            stale.append((age, n))
    if not (expired or stale or unknown):
        print(f"stale: nothing older than {days} days")
        return 0
    if expired:
        print("expired:")
        for n in expired:
            print(f"  {n['label']}  (expires {n['expires']}) - re-verify or delete")
    if stale:
        print(f"not updated in {days}+ days:")
        for age, n in sorted(stale, key=lambda x: -x[0]):
            print(f"  {age:>4}d  {n['label']}  last {n['updated']}")
    if unknown:
        print("no updated date:")
        for n in unknown:
            print(f"  {n['label']}")
    return 1 if expired else 0


def cmd_stats() -> int:
    items = _all_notes()
    map_size = len(INDEX.read_text(encoding="utf-8-sig")) if INDEX.is_file() else 0
    total = sum(n["path"].stat().st_size for n in items)
    print(f"notes      {len(items)} in {len(domain_dirs())} domain(s)")
    print(f"map        {map_size} / {MAX_MAP} chars")
    print(f"knowledge  {total / 1024:.1f} KB")
    mem = [p for p in MEM.glob("*.md") if p.is_file()]
    print(f"memory     {len(mem)} files, {sum(p.stat().st_size for p in mem) / 1024:.1f} KB")
    newest = max((n["updated"] for n in items if n["updated"]), default="never")
    print(f"newest     {newest}")
    print("")
    for n in sorted(items, key=lambda n: -(n["path"].stat().st_size)):
        print(f"  {n['path'].stat().st_size:>7} B  {n['lines']:>3} lines  {n['label']}")
    return 0


def cmd_dupes() -> int:
    """Near-duplicate evidence lines: same text after normalisation."""
    seen: dict[str, list[str]] = {}
    for p, _, line in iter_text():
        text = line.strip()
        if not text.startswith("- ") or len(text) < 40:
            continue
        key = re.sub(r"^- \d{4}-\d{2}-\d{2}:\s*", "", text)
        key = re.sub(r"\s+", " ", key.lower()).strip(" .")
        if len(key) < 30:
            continue
        seen.setdefault(key, []).append(p.name)
    groups = {k: v for k, v in seen.items() if len(v) > 1}
    if not groups:
        print("dupes: none")
        return 0
    print(f"dupes: {len(groups)} repeated line(s)")
    for key, files in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  x{len(files)}  {', '.join(sorted(set(files)))}")
        print(f"        {key[:150]}")
    return 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, rest = argv[1], argv[2:]
    if cmd == "index":
        return cmd_index()
    if cmd == "lint":
        return cmd_lint()
    if cmd == "stats":
        return cmd_stats()
    if cmd == "dupes":
        return cmd_dupes()
    if cmd == "project":
        return cmd_project(rest[0] if rest else None)
    if cmd == "pending" and rest:
        session = ""
        words = []
        i = 0
        while i < len(rest):
            if rest[i] == "--session" and i + 1 < len(rest):
                session = rest[i + 1]
                i += 2
            else:
                words.append(rest[i])
                i += 1
        return cmd_pending(" ".join(words), session)
    if cmd == "review":
        promote = topic = None
        clear = False
        i = 0
        while i < len(rest):
            if rest[i] == "--promote" and i + 1 < len(rest):
                promote = rest[i + 1]
                i += 2
            elif rest[i] == "--topic" and i + 1 < len(rest):
                topic = rest[i + 1]
                i += 2
            elif rest[i] == "--clear":
                clear = True
                i += 1
            else:
                i += 1
        return cmd_review(promote, topic, clear)
    if cmd == "consolidate":
        return cmd_consolidate("--apply" in rest)
    if cmd == "search" and rest:
        return cmd_search(" ".join(rest))
    if cmd == "show" and rest:
        return cmd_show(rest[0])
    if cmd == "append" and len(rest) >= 2:
        source = ""
        force = "--force" in rest
        words = []
        i = 0
        while i < len(rest):
            if rest[i] == "--source" and i + 1 < len(rest):
                source = rest[i + 1]
                i += 2
            elif rest[i] == "--force":
                i += 1
            else:
                words.append(rest[i])
                i += 1
        if len(words) < 2:
            print("append: need <topic> <text> [--source <ref>] [--force]")
            return 2
        return cmd_append(words[0], " ".join(words[1:]), source, force)
    if cmd == "owner" and len(rest) >= 2:
        return cmd_owner(rest[0], rest[1])
    if cmd == "stale":
        days = 30
        if "--days" in rest:
            at = rest.index("--days")
            if at + 1 < len(rest):
                try:
                    days = int(rest[at + 1])
                except ValueError:
                    print("stale: --days takes a number")
                    return 2
        return cmd_stale(days)
    if cmd == "similar" and rest:
        top = 5
        full = "--answers" not in rest
        keep = "--keep" in rest
        embed_mode = "auto"
        if "--lex" in rest:
            embed_mode = "off"
        words = []
        i = 0
        while i < len(rest):
            if rest[i] == "--top" and i + 1 < len(rest):
                try:
                    top = int(rest[i + 1])
                except ValueError:
                    print("similar: --top takes a number")
                    return 2
                i += 2
            elif rest[i] in ("--answers", "--lex", "--keep"):
                i += 1
            else:
                words.append(rest[i])
                i += 1
        if not words:
            print("similar: need a query")
            return 2
        return cmd_similar(" ".join(words), top, full, embed_mode, keep)
    if cmd == "embed":
        action = "rebuild"
        if "--status" in rest:
            action = "status"
        elif "--stop" in rest:
            action = "stop"
        elif "--start" in rest:
            action = "start"
        return cmd_embed(action, "--keep" in rest)
    if cmd == "rmfact" and rest:
        return cmd_rmfact(" ".join(w for w in rest if w != "--force"), "--force" in rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
