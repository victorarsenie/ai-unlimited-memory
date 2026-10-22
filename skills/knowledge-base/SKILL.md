---
name: knowledge-base
description: "Persistent knowledge and memory in ai-unlimited-memory — read the injected map before a task, open the matching note, append durable findings with kb.py in the same turn. Use whenever work produces a durable fact, path, number, decision or gotcha, or when a task touches a known topic."
version: 3.0.0
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
   the file. If nothing matches: `python kb.py search "<keyword>"`.
2. **Write the moment you learn something durable** — a decision, a measurement, a
   path, a version, a gotcha, a user rule. Same turn:
   `python kb.py append <topic> "<one line with the number and why>"`, then
   `python kb.py index`.
3. **Delete wrong facts explicitly**: `kb.py rmfact "<text>"`. Never leave a stale
   line hoping a later note overrides it.

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
