---
name: knowledge-base
description: "Persistent knowledge and memory in ai-unlimited-memory — read the injected map before a task, open the matching note, save durable findings with the kb_append tool (or kb.py) in the same turn, queue uncertain ones with kb_pending. Use whenever work produces a durable fact, path, number, decision or gotcha, or when a task touches a known topic."
version: 3.1.0
author: Victor
license: MIT
platforms: [windows, linux, darwin]
metadata:
  hermes:
    tags: [memory, notes, persistence, knowledge-base, context, compaction]
    category: memory
    related_skills: []
---

# Knowledge base

The corpus lives at `MEMORY_HOME` (default
`E:\AI\memory\ai-unlimited-memory`), outside any harness, so every harness reads
the same notes. `knowledge/` holds one note per topic; `memory/` holds the small
always-on files (profile, projects).

## The contract

`knowledge/INDEX.md` is **generated** from the notes' front matter by
`python kb.py index`. A harness hook injects it every turn, so it survives
compaction. Treat the injected copy as a table of contents, never as the answer.

1. **Route, then read.** Match the question against the `answers` column, then read
   the file. If nothing matches, in this order:
   1. `kb_similar("<question>")` — BM25 over the full notes, no model and no
      process. It returns note files; open the first one.
   2. `kb_search` (tool) or `python kb.py search "<term>"` — exact strings,
      numbers, versions, paths that BM25 may rank second.
   3. Both indexes are **lexical and English**. For a question in Romanian,
      translate the keywords to English before searching ("cât de repede
      decodează" -> "decode speed"); otherwise nothing matches.
   Never answer from the ranking alone: it names a file, it does not state facts.
2. **Write the moment you learn something durable** — a decision, a measurement, a
   path, a version, a gotcha, a user rule. Same turn:
   `kb_append(topic, "<one line with the number and why>")` — it refreshes the map
   itself. Without the MCP tools, the CLI is the same corpus:
   `python kb.py append <topic> "..."`. Add `source=` (CLI: `--source <ref>`) when
   the fact rests on a log, config, URL or commit rather than on the conversation.
3. **Unsure where it belongs, or unverified?** `kb_pending(text)` queues it in
   `knowledge/pending/<date>.md`. It is never injected. The user promotes it with
   `kb.py review --promote N --topic <note>` or drops it with `--clear`.
4. **Delete wrong facts explicitly**: `kb_rmfact` (tool) or
   `kb.py rmfact "<text>"`. Never leave a stale line hoping a later note overrides
   it.
5. **Repo-scoped facts go to the project overlay.** When the injected context shows
   a `# Project overlay:` map, the facts that are only true in this repository
   (paths, local commands, current state) belong in
   `knowledge/projects/<slug>/`, not in the global notes. Create
   `project.md` there with `paths:` (absolute) or `remotes:` (git origin) so the
   overlay is detected; `kb.py project` prints the slug for a directory.

## Note format

Every note starts with front matter; without `answers:` it is not indexed and
`kb.py lint` fails:

```markdown
---
title: MoE expert caching
answers: merged expert cache is a loss on this machine
updated: 2026-10-22
tags: [moe, cache, speed]
---

# MoE expert caching

**Answer.** The one or two sentences that settle the question.

## Evidence
- 2026-10-21: cache 0 = 36-37.5 t/s, 4096 MiB = 24-24.5 t/s (four runs each).
```

## What belongs here

- Hard numbers (speeds, context ceilings, VRAM, versions, sizes) and how measured.
- Paths that are not obvious, and why they are there.
- Decisions plus the reason, especially reversed ones.
- Gotchas that cost time once and would cost it again.
- User rules and preferences.

Not here: secrets, huge logs, code that lives in a repo, anything already in a
project's `AGENTS.md`. Link the path instead of copying it.

## Budget

The map is capped at 3,000 characters. If `kb.py index` trims rows, it prints a
warning and `kb.py lint` lists the orphaned notes: merge or archive them, do not
raise the cap.

## Adding a topic

1. Create `knowledge/<topic>.md` with the front matter above and an `**Answer.**`
   paragraph.
2. `python kb.py index`.
3. Link it from a related note so the corpus stays navigable.

## Maintenance

- `python kb.py stats` — note count, map budget, per-note size, newest write.
- `python kb.py dupes` — repeated evidence lines after normalisation.
- `python kb.py consolidate` — near-duplicate clusters (Jaccard ≥ 0.85); add
  `--apply` to keep the fullest line and drop the rest. Run `index` afterwards.
- `python kb.py review` — queued candidates; `--promote N --topic <note>` or
  `--clear`.
- `python kb.py stale [--days N]` — notes not touched in N days, plus notes whose
  `expires:` date has passed. `lint` fails on an expired note until you re-verify
  or delete it.
- `python kb.py project [path]` — which overlay applies here.
- `python kb.py similar "<question>"` — BM25 ranking over the full notes when the
  map gives no match; `--answers` restricts it to the Answer block. It names
  notes, it does not answer: open the note.
- `python kb.py embed --status` — the optional embedder (semantic recall, 940 MB
  resident). Off by default and never started by `similar`; only `--start` runs
  it, and it must not run while Strata's experts are pinned.
