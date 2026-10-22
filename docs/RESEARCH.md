# Persistent memory and a voice interface for local agent harnesses

Research note, October 2026. Local-first AI on a single Windows workstation:
RTX 5070 Ti 16 GB, 32 GB RAM, models served by llama.cpp / Strata on the same box.

The question: can one persistent memory system serve several agent harnesses
(OpenCode, Hermes, anything installed later), and can the same system carry a
voice interface without giving up local models or privacy?

---

## 1. Why this is not a solved problem

Every harness ships its own memory, and each one is optimised for its own loop:

- **OpenCode** runs `opencode-mem`, a local embedding store
  (`Xenova/nomic-embed-text-v1`) that injects notes by similarity through the
  `chat.message` hook, plus an injection at compaction. Recall is automatic but
  ranked by similarity, so it is not guaranteed to surface the decision you need.
- **Hermes** keeps 2,200 characters of personal notes and a 1,375-character user
  profile in the system prompt, plus a `knowledge/` folder whose `INDEX.md` is
  re-injected every turn by a `pre_llm_call` hook (capped around 2,600
  characters). Exact and deterministic, but only as good as what was written down.
- **Claude Code** has no built-in long-term memory at all; the ecosystem sells it
  as an add-on (see the Memory Vault below).

The result is predictable: the same fact gets stored three times, in three
formats, and none of the copies is canonical. A decision made in one harness is
invisible in another, and after a context compaction it may be invisible in the
same one.

## 2. Prior art reviewed

| project | memory model | voice | dependency | what it gets right |
|---|---|---|---|---|
| **backtalk** (jaredrhod) | none of its own; borrows the agent's | push-to-talk, local faster-whisper + Kokoro, sentence streaming, spoken permission gate | Claude Agent SDK, paid Claude plan | the voice loop's feel: 1–2 s to first audio, interrupt, approvals spoken |
| **AI Memory Vault** (jaredrhod) | Obsidian vault of notes + `CLAUDE.md` boot config + `VAULT-INDEX.md`; per-job "priming" lists | — | Claude Code (portable with rough edges) | per-task priming: a stored reading list per recurring job |
| **JARVIS 4.0 / Mark-LVI** (FatihMakes) | "recallable memory": prompt carries what fits, the rest is looked up on demand from a local search; fact-level memory panel with delete | Gemini Live by default; own STT+LLM+TTS engine supported | Python; Gemini key by default, local providers optional | the memory model matches what we concluded; provider abstraction incl. llama.cpp/vLLM |
| **Hermes** (Nous Research) | 2.2k + 1.4k chars always in prompt; `knowledge/` + injected index; FTS5 over sessions | "Hey Hermes" wake word (off by default), local STT, TTS tool | none; uses whatever model is running | memory that survives compaction without discipline |
| **OpenCode** | `opencode-mem` embeddings, similarity injection | none built in | — | retrieval that can resurface what was never stored |
| **pi-hermes-memory** (prior local attempt) | `MEMORY.md` (43 KB), `USER.md`, `failures.md`, `sessions.db` | — | pi harness | file + SQLite hybrid, in production long enough to fail visibly |
| **PersonalMemory** (own project, 2026-10) | SQLite canonical (`INDEX/personal_memory.sqlite3`), `RAW/` `DERIVED/`, ChatGPT archive import, checkpoints | — | Python 3.12, local API on 127.0.0.1:8765 | a real schema, migrations, and a compliance-style import path |

## 3. Findings

**3.1 Files or a database is a false choice.** The working systems converge on
the same split: files for what a model reads and a human edits, SQLite for what
needs transactions, full-text search, or volume. pi reached it by accident
(`MEMORY.md` plus `sessions.db`); PersonalMemory reached it deliberately
(SQLite canonical for conversation data); Mark-LVI implements the public half in
one sentence — the prompt carries what fits, the rest is searched on demand.
The architecture is: **files are canonical, the index is derived and
rebuildable**.

**3.2 Unbounded storage is not unbounded context.** The vault is described as
"no size ceiling"; Hermes caps its injected map at ~2,600 characters; our own
addendum is 158 KB (≈40k tokens) and could never be injected wholesale. What
makes "unlimited memory" work is an index small enough to always be present and
notes read at full fidelity on demand.

**3.3 Discipline fails; hooks do not.** The 43 KB `MEMORY.md` from the earlier
pi setup contains the same user-profile sentence four times — every session
appended a new copy because nothing consolidated. Hermes solved the injection
side with a hook that re-sends the map every turn, so memory does not depend on
the model choosing to remember. Both halves are needed: an automatic injection,
and a write path that consolidates instead of appending.

**3.4 The voice layer is portable; the brain is not.** backtalk's ears and mouth
are local (faster-whisper, Kokoro) but its brain is the Claude Agent SDK, which
requires a paid Claude plan. Everything else in it — push-to-talk, sentence
chunking, one long-lived audio stream, a spoken permission gate, turn-drain
after an interrupt — is harness-agnostic. OpenCode exposes the equivalent
primitives over HTTP: `POST /session/:id/prompt_async`, an SSE `/event` stream,
`POST /session/:id/abort`, and `/session/:id/permissions/:permissionID`.

**3.5 Hands-free needs a wake word, not just VAD.** The same project's own
troubleshooting notes warn that an open mic transcribes the room, the TV and its
own reply. The host machine's speakers and microphone are the same device, and
Windows has no dependable echo cancellation for this. A wake word
(`openwakeword`, ~2 MB, CPU) plus a mute-while-speaking flag is the minimum
before an always-on mic is acceptable.

**3.6 The local model choice is a quality question, not a speed one.** The
coder models are documented as weaker outside code, and published tests agree.
For conversation the candidates are the general 27B variants; a half-second
difference in first audio is not a reason to accept worse answers. Speed is a
veto threshold (unusable if several seconds to first audio), not a ranking.

## 4. Proposed design

Two layers, both plain files, both readable by any harness:

**Memory** — small, always injected. Personal notes, current projects, standing
decisions. Rewritten, never appended blindly; a few kilobytes at most.

**Knowledge** — large, indexed. Topic notes with an `Answer` block, evidence,
negative results, and open questions. An `INDEX.md` of one-line hooks is
generated from the notes and injected every turn; the notes themselves are read
on demand.

**Jobs** — a third small layer borrowed from the vault: per-task priming lists
("before a bench round, read protocol, model arms, instruments"). Neither Hermes
nor OpenCode has this, and it is the cheapest way to make recurring work
consistent.

**Adapters** — one per harness, all doing the same thing: read the map, prepend
it. A local plugin on OpenCode's `chat.message` hook; Hermes' existing knowledge
hook retargeted; a one-line pointer for harnesses with no plugin system. The
fallback requires no code at all, because the map is a file and `grep` works in
any shell.

**Index** — generated, capped at 3,000 characters, and refusing to grow past it
(printing the stalest entries to merge instead). SQLite FTS5 is available as a
rebuildable cache for large archives, never as the only copy.

**PersonalMemory** — the existing SQLite system stays the canonical store for
conversation archives and derived checkpoints, and exposes them through its
read-only API. It is not replaced by the file layer; the two answer different
questions (what was said vs. what was learned).

## 5. Measurement note: report unique bytes, not names

A practical detail that cost an hour: model directories on this machine use
hard links, so the same 70 GB of weights appear under two paths. `Get-ChildItem`
and Explorer count both names, inflating a 113 GB tree to 188 GB. The truth is
the volume's free space; per-folder numbers need the file identity
(volume + file index), not the path. A 40-line Python helper now reports unique
bytes and how much is hidden by links. The same trap applies to any migration:
copying a tree between volumes turns every hard link into a full copy.

## 6. What was deliberately not built

- A second embedding store. OpenCode already runs one; a curated map competes
  with it rather than complementing it.
- A custom wake word. Training needs hours of positive samples; a pretrained
  phrase is a config value.
- Spoken approvals in the first version of any voice loop. Tool permissions that
  stall with a visible terminal message are safer than a spoken "yes" that the
  room can produce.
- Any dependency on a hosted model for the memory path. The corpus is local
  markdown and SQLite; the voice may use whatever model is running.

## 7. Next steps

1. Finish consolidating the machine's research corpus (four overlapping
   documents, ~1.1 MB) into topic notes with a generated map.
2. Wire the map into both harnesses and verify with ten questions that are only
   answerable from the knowledge base — pass means ≤2 tool calls and no
   invention.
3. Compare the two general 27B arms on spoken-style prompts, ranked by answer
   quality with latency as a veto.
4. Build the voice loop against OpenCode's server API (push-to-talk first, wake
   word after), reusing the documented failure modes: key-repeat handling, one
   long-lived audio stream, turn drain after abort, permission routing, mic
   generation counter.

## Sources

- jaredrhod, `backtalk` — https://github.com/jaredrhod/backtalk (readme, TROUBLESHOOTING, architecture notes)
- jaredrhod, `ai-memory-vault` — https://github.com/jaredrhod/ai-memory-vault (readme, templates)
- FatihMakes, `Mark-LVI` (JARVIS 4.0) — https://github.com/FatihMakes/Mark-LVI (readme, module layout)
- Nous Research, Hermes — local installation, `config.yaml`, `knowledge/`, `SOUL.md`
- OpenCode — server API and plugin hooks, https://opencode.ai/docs/server, /docs/plugins
- Local measurements: coder 71 t/s sustained; 27B-class 42.8 t/s on a 16 GB card; 12 GB card with expert spill 41–46 t/s on code
