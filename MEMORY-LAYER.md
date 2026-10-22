# Extended memory layer

This repository holds two things that belong together:

1. **The archive** — `src/personal_memory/`, the SQLite store of imported
   conversations, with provenance (unchanged by this layer).
2. **The knowledge layer** — `knowledge/`, `memory/`, `kb.py` and `adapters/`,
   added 2026-10-22. It is what an agent actually reads every turn.

The assistant (character, voice, initiative) lives in a separate repository:
`victorarsenie/jarvis`. It consumes this layer; it does not own it. The persona is
not stored here: `memory/` holds facts about the user, not the assistant's
character.

## Why two layers

| layer | size | injected | lifetime |
|---|---|---|---|
| `memory/` | kilobytes | every turn | rewritten (profile, projects) |
| `knowledge/` | unbounded | map every turn, note on demand | appended, dated |
| archive (SQLite) | gigabytes | never wholesale | forever |

A fact must survive compaction to be useful, so the map is re-sent every turn by a
harness hook instead of relying on the model to remember it. The archive is where
the verbatim conversation stays; it is searched, not injected.

Files are canonical. `knowledge/INDEX.md` is generated; delete it and
`python kb.py index` rebuilds it from the notes' front matter.

## Commands

```powershell
python kb.py index                  # rebuild knowledge/INDEX.md (<= 3000 chars)
python kb.py lint                   # structure + map consistency
python kb.py search "expert cache"  # search notes and memory
python kb.py show local-llm         # print one note
python kb.py append local-llm "text"     # dated entry under Evidence
python kb.py rmfact "wrong fact"         # delete every line containing it
```

## Note format

```markdown
---
title: MoE expert caching
answers: merged expert cache is a loss on this machine
updated: 2026-10-22
tags: [moe, cache, speed]
---

**Answer.** One or two sentences that settle the question.

## Evidence
- 2026-10-21: cache 0 = 36-37.5 t/s, 4096 MiB = 24-24.5 t/s (four runs each).
```

Without `answers:` a note is not on the map and `kb.py lint` fails.

## Harnesses

- **Hermes**: `adapters/hermes/knowledge-index.py` is a `pre_llm_call` hook. It
  reads `MEMORY_HOME` (default `E:\AI\memory\ai-unlimited-memory`), injects
  `memory/*.md` and `knowledge/INDEX.md`. Install with
  `adapters/hermes/install.ps1`; it backs up the previous hook and writes a shim.
- **OpenCode**: `adapters/opencode/knowledge-index.js` pushes a synthetic text
  part on `chat.message`, the same mechanism `opencode-mem` uses.

## Privacy

`knowledge/`, `memory/` and the imported data are **not** tracked: personal notes
stay on the machine that owns them. Only code, schema and synthetic examples are
committed. See `.git/info/exclude` and the repository `.gitignore`.

## Design

`docs/DESIGN.md` records the reasoning, the rejected alternatives (vectors-only
recall, silent summarisation) and the retrieval protocol.
