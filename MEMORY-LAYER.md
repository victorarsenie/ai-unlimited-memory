# Extended memory layer

This repository holds two things that belong together:

1. **The archive** â€” `src/personal_memory/`, the SQLite store of imported
   conversations, with provenance (unchanged by this layer).
2. **The knowledge layer** â€” `knowledge/`, `memory/`, `kb.py` and `adapters/`,
   added 2026-10-22. It is what an agent actually reads every turn.

The assistant (character, voice, initiative) lives in a separate repository:
`victorarsenie/muther`. It consumes this layer; it does not own it. The persona is
not stored here: `memory/` holds facts about the user, not the assistant's
character.

## Why two layers

| layer | size | injected | lifetime |
|---|---|---|---|
| `memory/` | kilobytes | every turn | rewritten (rules, profile, projects) |
| `knowledge/` | unbounded | map every turn, note on demand | appended, dated |
| archive (SQLite) | gigabytes | never wholesale | forever |

A fact must survive compaction to be useful, so the map is re-sent every turn by a
harness hook instead of relying on the model to remember it. The archive is where
the verbatim conversation stays; it is searched, not injected.

Files are canonical. `knowledge/INDEX.md` is generated; delete it and
`python kb.py index` rebuilds it from the notes' front matter. The map lists
**domains** (`models/`, `machine/`, `assistant/`, `memory/`, `workflow/`,
`projects/`, `research/`); each domain has its own generated `INDEX.md`, read on
demand, so the injected map stays ~1.4k chars however many notes exist.

## Commands

```powershell
python kb.py index                  # rebuild knowledge/INDEX.md (<= 3000 chars)
python kb.py lint                   # structure + map consistency
python kb.py stats                  # note count, budget, per-note size
python kb.py search "expert cache"  # search notes and memory
python kb.py show local-llm         # print one note
python kb.py append models/speeds "text"  # dated entry under Evidence
python kb.py append models/speeds "text" --source <ref>  # with provenance
python kb.py rmfact "wrong fact"         # delete every line containing it
python kb.py pending "candidate"         # queue for review (never injected)
python kb.py review                      # list candidates
python kb.py review --promote 1 --topic local-llm
python kb.py review --clear
python kb.py dupes                       # repeated evidence lines
python kb.py consolidate [--apply]       # near-duplicate merge proposals
python kb.py project                     # overlay matching the current directory
python kb.py project E:\AI\bench         # overlay for a given directory
python kb.py stale [--days 30]           # untouched notes and passed expires dates
python kb.py similar "expert cache"      # BM25 over the notes, no process
python kb.py similar "spill" --answers   # restrict to the Answer block
python kb.py embed --status              # optional embedder state (off by default)
```

## Write paths

Three ways in, one corpus:

1. **MCP tools** â€” `adapters/mcp/server.py` exposes `kb_search`, `kb_append`,
   `kb_pending`, `kb_review`, `kb_rmfact`, `kb_stats`, `kb_stale` over stdio
   JSON-RPC (no dependencies). OpenCode registers it as `ai-memory` in
   `opencode.jsonc`; any MCP client can use it. This is the preferred path:
   saving is a tool call, not a shell permission prompt.
2. **CLI** â€” the same functions, for scripts and harnesses without MCP.
3. **Automatic capture** â€” the OpenCode plugin watches the last user message for
   phrases like "remember", "decision", "gotcha" and queues the text in
   `knowledge/pending/<date>.md`. Candidates are never injected and never merged
   automatically; promotion is one command. Compaction checkpoints and harness
   wrappers are filtered out by length and marker.

## Recall beyond the map

The map holds 3,000 characters, so notes eventually fall off it. Two dependency-free
routes cover that, both reading files only â€” no process, no index, no network:

- `kb.py search "<term>"` greps every note and memory file.
- `kb.py similar "<question>"` ranks notes with BM25 over the whole note
  (`--answers` narrows it to the Answer block). Length normalisation is what makes
  this usable: without it the 26 KB `local-llm` note wins every query by sheer size.

Measured 2026-10-23 on eight English questions and two Romanian ones, 12 notes:
BM25 top-1 was 7/8 in English (6/8 with `--answers`) and 0/2 in Romanian. The
Romanian failure is structural, not a bug: BM25 compares tokens, and the corpus is
English. The instruction to translate keywords lives in the skill, where the model
can act on it.

**Optional embedder.** `kb.py embed --start` runs `llama-server --embeddings` with
`multilingual-e5`-class models; it measures 0.47 cosine for a Romanian question
against the matching English note versus 0.20 for an unrelated one, so it does close
the cross-language gap. It is **off by default** and nothing starts it implicitly:
the helper is ~940 MB resident, and this machine keeps ~20.5 GiB of Strata experts
pinned in the same RAM. Use it only when Strata is not serving, and stop it after.

## Project overlays

Facts that are only true in one repository do not belong in the global map: they
would be injected in every session and would push real topics out of the 3,000
char budget. They live in their own folder instead:

```
knowledge/projects/<slug>/
  project.md     front matter: title, answers, updated, paths, remotes
  <topic>.md     normal notes, same format as knowledge/*.md
  INDEX.md       generated by `kb.py index`, capped at 1,200 chars
```

`paths` are absolute directories; `remotes` are git origin URLs or fragments of
them. Detection runs on every turn and is deliberately narrow: the longest
matching `paths:` entry wins, and only if none matches is `git remote get-url
origin` consulted. No match means no overlay, so the cost in an unrelated
directory is zero.

Both harnesses inject the overlay **after** the global map, capped separately,
and only when the turn's working directory matches. `kb.py lint` checks that
every overlay has at least one `paths` or `remotes` entry, that each note carries
front matter and an `answers` line, and that its `INDEX.md` is current.

## Note format

```markdown
---
title: MoE expert caching
answers: merged expert cache is a loss on this machine
updated: 2026-10-22
expires: 2027-01-31
owner: agent
tags: [moe, cache, speed]
---

**Answer.** One or two sentences that settle the question.

## Evidence
- 2026-10-21: cache 0 = 36-37.5 t/s, 4096 MiB = 24-24.5 t/s (four runs each).
  (source: `logs/moe-cache-sweep.out`)
```

Without `answers:` a note is not on the map and `kb.py lint` fails.

`expires:` is optional and only for facts that stop being true on their own, such
as a version, a price or a rented machine. When the date passes, `kb.py lint`
fails and `kb.py stale` lists the note: re-verify it, or delete it. Never use
`expires:` to express "someone will edit this later" - that is what `updated:`
and `kb.py stale` are for.

`--source` is optional and belongs on every evidence line that rests on
something outside the conversation: a log, a config file, a URL, a commit, a
bench run. The line stays one sentence; provenance rides at the end in
parentheses, so `kb.py dupes` and `kb.py consolidate` still compare the facts.

## Ownership

`owner: human` marks a note the user wrote and maintains â€” `user.md` is the first
one. Agents read it freely but do not write it: `kb_append`, `kb_rmfact` and
`kb_consolidate` refuse or skip it, and `lint` counts protected notes so the set
stays visible. Notes without `owner:` are treated as `owner: agent`.

The rule exists because a rewrite is not recoverable from the note itself: an agent
that "tidies" a rule can change what the rule means. An explicit request from the
user overrides it â€” that ask is the permission. The write then carries
`--source "user asked in chat"` (or similar) so the note records that a human
approved the edit, and a long note should have its proposed line shown before the
write, not after. `kb.py owner <topic> human|agent` flips the flag.

## Operating rules live here, not in a harness config

`memory/rules.md` is the behaviour contract: working style, edit discipline,
reporting, boundaries, memory rules. Both adapters inject it first in every request,
so OpenCode and Hermes cannot drift apart, and a third harness only has to inject
the same file. Harness configs (`~/.config/opencode/AGENTS.md`, Hermes `SOUL.md`)
keep only what is genuinely harness-specific and point here; the OpenCode one also
tells the model to read this file directly if the injection is ever missing.

Sizes are capped per file (`rules` 3,200, `profile` 1,400, `projects` 1,800, map
3,000, overlay 1,200 chars) and the caps are deliberately above the current sizes:
a cap below the file silently truncates it, which is worse than a slightly larger
prompt.

## What lives where

Every artefact a harness needs has a canonical copy in this repository, so a wiped
config is rebuilt from here rather than reconstructed from memory. `recover.ps1`
checks and reinstalls all of it.

| installed path | canonical source here | installed by |
|---|---|---|
| `~/.config/opencode/plugins/knowledge-index.ts` | shim generated from `adapters/opencode/knowledge-index.js` | `adapters/opencode/install.ps1` |
| `~/.config/opencode/AGENTS.md` | `adapters/opencode/AGENTS.md` | `adapters/opencode/install.ps1` |
| `opencode.jsonc` â†’ `mcp.servers.ai-memory` | `adapters/opencode/mcp.ai-memory.jsonc` | printed by `install.ps1` (that file is not ours to rewrite) |
| `~/.config/opencode/skills/knowledge-base/SKILL.md` | `skills/knowledge-base/SKILL.md` | `skills/install.ps1` |
| `D:\Hermes\agent-hooks\knowledge-index.py` | shim generated from `adapters/hermes/knowledge-index.py` | `adapters/hermes/install.ps1` |
| `D:\Hermes\config.yaml` â†’ `hooks.pre_llm_call` | `adapters/hermes/hooks.snippet.yaml` | `adapters/hermes/install.ps1` (appends when `hooks:` is absent, otherwise prints) |
| `D:\Hermes\skills\memory\knowledge-base\SKILL.md` | `skills/knowledge-base/SKILL.md` | `skills/install.ps1` |
| injected context in every harness | `memory/rules.md` + `memory/profile.md` + `memory/projects.md` + `knowledge/INDEX.md` + project overlay | the adapters |

The data itself â€” `knowledge/`, `memory/`, the SQLite archive â€” never lives in a
harness config, so losing a config loses wiring, not memory.

## Harnesses

- **Hermes**: `adapters/hermes/knowledge-index.py` is a `pre_llm_call` hook. It
  reads `MEMORY_HOME` (default `E:\AI\memory\ai-unlimited-memory`), injects
  `memory/rules.md`, `memory/profile.md`, `memory/projects.md` and
  `knowledge/INDEX.md`, plus the project overlay when the cwd matches. Install with
  `adapters/hermes/install.ps1`; it backs up the previous hook and writes a shim.
- **OpenCode**: `adapters/opencode/knowledge-index.js` exports `buildContext()`
  (rules + memory + map + overlay) and `captureCandidate()`; the installed v2 shim
  (`~/.config/opencode/plugins/knowledge-index.ts`) pushes the context into
  `event.system` with an ephemeral cache hint and calls the capture on each
  request. Install with `adapters/opencode/install.ps1`.
- **Any MCP client**: run `adapters/mcp/server.py`; see *Write paths* above.

## Privacy

`knowledge/`, `memory/` and the imported data are **not** tracked: personal notes
stay on the machine that owns them. Only code, schema and synthetic examples are
committed. See `.git/info/exclude` and the repository `.gitignore`.

## Design

`docs/DESIGN.md` records the reasoning, the rejected alternatives (vectors-only
recall, silent summarisation) and the retrieval protocol.
