# Design: one memory layer, many harnesses

## Problem

Each agent harness has its own memory, and each solves a different third of the
problem:

- **OpenCode** has an embedding-based recall plugin (`opencode-mem`): semantic
  search, but nothing is inspectable or deletable as a fact, and another harness
  cannot read it.
- **Hermes** has capped notes plus a `pre_llm_call` hook that injects a markdown
  index: cheap and transparent, but the corpus lives inside `D:\Hermes` and dies
  with that harness.
- **The conversation archive** (`src/personal_memory/`, same repository) is a SQLite
  conversation store with provenance: the right place for *what was said*, a poor
  place to hand an agent every turn.

The failure mode observed on this machine: a 43 KB `MEMORY.md` in which the same
profile sentence appears four times, because nothing ever consolidated it.

So the missing layer is not another store. It is a **canonical, small, inspectable
corpus plus a map cheap enough to inject every turn**, with adapters that read it.

## Three layers, three lifetimes

| layer | what it holds | lifetime | owner |
|---|---|---|---|
| transcript | everything ever said, verbatim | forever | this repo, `src/` (SQLite) |
| knowledge | one note per topic, an answer at the top | appended, dated | this repo, `knowledge/` |
| memory | profile, active projects | rewritten | this repo, `memory/` |

Only the last two are injected. The transcript is searched when a note points at
it, never injected wholesale. The persona — character, tone, initiative — is not
memory: it lives in the assistant repository (`jarvis`), because it must not change
when facts do.

Rule: **files are canonical; every index is derived and rebuildable.** Delete
`INDEX.md` and `kb.py index` reconstructs it from the notes' front matter. A
database that cannot be rebuilt from the files is a design error, not a feature.

## The map

`knowledge/INDEX.md` is generated, capped at 3,000 characters, and injected into
every turn. Each row is `topic | file | answers | tags`, so the model can decide
*which* note to open without opening any.

Two deliberate consequences:

1. **The cap is visible.** When the map would exceed 3,000 characters, `kb.py`
   trims the least recently updated rows and says so; `kb.py lint` then reports
   those notes as off-map. Growth becomes a forced decision (merge or archive),
   not a slow leak.
2. **The map cannot drift.** It is regenerated from front matter, so a note
   without `answers:` is not indexed and fails lint. There is no second place to
   update.

This is the part taken from Mark-LVI: what fits goes in the prompt, the rest is
looked up on demand — but the lookup is a file read, not an embedding query, so it
is reproducible and auditable.

## Why not embeddings (for this layer)

Embeddings answer "what is similar?", which is not the question an agent has. The
agent needs "is there a decision about X, and what was it?". A map row with an
`answers` line answers that in one line of prompt budget. Embeddings also hide
provenance and make deletion approximate; `kb.py rmfact` deletes exact lines.

Semantic recall stays available where it belongs: the archive's index over
transcripts.

## Retrieval protocol

1. Map arrives with the turn (adapter, not model discipline).
2. If a row matches the task, read that file before answering.
3. If the finding is durable, `kb.py append <topic> "<text>"` in the same turn,
   then `kb.py index`.
4. If a fact is wrong, `kb.py rmfact "<text>"` — and say so.

Step 3 is the one agents skip. It is stated in the injected header, in the note
template, and in `jobs/` — three places, because one is not enough.

The harness-level alternative — a skill telling the model "remember to save" —
was tried and fails: after compaction the instruction is gone with everything
else. Injection is the only mechanism that survives compaction.

## Adapters

Both adapters do the same thing with different transport:

| harness | hook | contract |
|---|---|---|
| Hermes | `pre_llm_call` | JSON on stdin, `{"context": "..."}` on stdout |
| OpenCode | `chat.message` | push a synthetic text part onto `output.parts` |

The Hermes installation is a three-line shim that `runpy`s the adapter inside this
repo, so there is exactly one implementation and `git pull` updates Hermes.

`MEMORY_HOME` (default `E:\AI\memory\ai-unlimited-memory`) means the corpus can move without touching
code. Porting to a third harness is one file that reads `INDEX.md`.

## Privacy boundary

Personal notes and memory are **gitignored**; the repository holds code, schema
and synthetic examples. This mirrors the rule already used by the archive project:
public repositories and portfolio material use synthetic data only.

## Deliberate omissions

- No vector store, no server, no daemon. `kb.py` is stdlib-only and runs in
  milliseconds.
- No write path from the model into the transcript. Conversation archiving belongs
  to the archive's importer, not to a hook that could silently rewrite history.
- No automatic summarisation of notes. Consolidation is a human decision because
  the failure mode being avoided is exactly un-reviewed machine summarising.
