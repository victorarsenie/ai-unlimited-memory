# Memory system review: where we stand and what to take

Reviewed 2026-10-22 against `opencode-mem`, `opencode-agent-memory`,
`opencode-plugin-simple-memory`, `opencode-supermemory` and the Mem0 OpenCode
plugin. Verdict first, evidence after.

## Verdict

Not the best overall. Ours wins on **auditability, portability and cost**, and is
weakest on exactly the thing that caused the complaint: **nothing captures what
the model learns unless the model chooses to write it down**. The gap is write
automation and consolidation, not storage.

| | ours (ai-unlimited-memory) | opencode-mem | agent-memory (Letta blocks) | simple-memory | supermemory | mem0 |
|---|---|---|---|---|---|---|
| storage | markdown files | Turso vectors | markdown blocks | logfmt files | cloud | cloud |
| capture | manual (`kb.py append`) | auto at idle, LLM extraction | manual, 5 tools | manual, optional "remember" | auto every N turns | auto every 3rd prompt |
| retrieval | full map + read note | embedding search | injected blocks + journal search | scored recall, budgeted | profile + project + recall | semantic search |
| consolidation | none (map trims) | dedupe on write | none | exact duplicates only | hosted | add/update/delete ops |
| scopes | one corpus + tags | project shards, all-projects | global + project blocks | user/project | user/project | project/session/global |
| deletion | `rmfact` | UI + API | `memory_replace` | `forget` + audit log | `forget` | `delete_memory` |
| provenance | dated lines | memory→prompt timeline | entry per session | audit log | timeline | metadata |
| UI | none | web UI + stats | none | none | TUI footer | commands |
| deps | stdlib Python | ~0.5-2 GB RAM embeddings | Bun + embeddings for journal | none | API key + network | API key + network |
| harness-agnostic | yes (Hermes + OpenCode) | OpenCode only | OpenCode only | OpenCode only | OpenCode + others | multi |

What that means in practice:

- If the measure is "does it remember without me asking", supermemory and
  opencode-mem are ahead today.
- If the measure is "can I read, diff, delete and move every fact, and use the
  same corpus from another harness", ours is ahead of all of them.
- The right target is not to become opencode-mem. It is to close the capture gap
  while keeping files canonical.

## Ideas worth taking, in order

### 1. Write path for the agent (highest value)

Today the model must run a shell command to save anything; in OpenCode that is a
permission prompt, so it rarely happens. `opencode-agent-memory` and
`simple-memory` both expose memory as **tools**, not shell.

- Register `kb_append`, `kb_search`, `kb_rmfact` as OpenCode tools in the same
  plugin that injects the map.
- Keep the CLI as the source of truth; the tools are thin wrappers.
- This alone converts "the model could save" into "the model saves".

### 2. Capture without auto-merging

supermemory captures every N turns; opencode-mem runs an LLM extraction at idle.
Both risk the failure we already saw (43 KB `MEMORY.md`, same sentence four
times). Take the capture, not the write-through:

- At session end (or every N turns), write candidates to
  `knowledge/pending/<date>-<session>.md` — reviewable, never in the map.
- `kb.py review` shows candidates with source session, one line each; `--promote`
  appends the accepted ones and deletes the rest.
- Nothing reaches the canonical corpus without one human look.

### 3. Consolidation (`kb.py consolidate`)

`simple-memory compact` removes exact duplicates; Mem0 runs add/update/delete
decisions. Our normalised-line check (`kb.py dupes`, added 2026-10-22) is the
first step.

- Extend to near-duplicates: token-set Jaccard over evidence lines, threshold
  ~0.85, print merge proposals.
- `--apply` rewrites the merged line once, keeps the newest date, and lists what
  it dropped.
- Run it in `lint` as a warning, never silently.

### 4. Recall beyond the map

`agent-memory` keeps an append-only journal with semantic search; ours loses
notes the moment they are trimmed from the 3,000-character map.

- Cheapest: expose `kb.py search` as a tool so the model can grep on demand.
- Optional second index: embed note titles + `answers` only (not the body),
  stored locally, rebuilt by `kb.py index`; the body stays file-only. Small
  vectors, no new canonical store.
- Do not embed the corpus; that reintroduces the thing we rejected.

### 5. Project scoping

opencode-mem shards by git repo (and needed `migrate` tools when paths moved — a
warning). mem0/supermemory scope per project by default.

- Add `knowledge/projects/<slug>/*.md` overlays, merged into the map only when
  the working directory matches; the global map stays small.
- Slug from the git remote, not the path (our own path migrations are evidence).

### 6. Provenance and staleness

- `kb.py append --source <archive-id|session-id>` stores where a fact came from;
  PersonalMemory already has the archive to point at.
- `kb.py review` also lists notes untouched for N days, notes with empty
  `## Open`, and facts past an optional `expires:` date.

### 7. Cache-aware injection (cost)

Re-injecting 3.6 KB on every model request invalidates the provider prompt cache;
`opencode-mem` injects on the first turn or explicitly `always`, and
`agent-memory` freezes blocks per session for exactly this reason.

- Inject fully when: first request, map hash changed, or after compaction.
- Between those, inject nothing (the earlier system part is already cached in the
  session) — and log the decision so it is visible.
- Keep `always` as a config switch for debugging.

### 8. Small things

- `<private>...</private>` blocks: strip before injection (supermemory).
- `kb.py stats` for the status rail (added 2026-10-22: note count, map budget,
  per-note size, newest write).
- Audit line for every deletion, not just a silent rewrite (simple-memory).
- Encryption at rest only if the corpus ever leaves the machine's user profile;
  not now.

## What not to take

- **Embeddings as the primary store.** The failure that started this project is
  invisible with vectors; files are diffable and reviewable.
- **Hosted memory.** supermemory/mem0 put the corpus behind an API key; that is
  the opposite of the requirement.
- **Auto-merge without review.** Capture is fine; silent consolidation is how
  duplicates become permanent.
- **Per-path project shards.** opencode-mem ships migration tooling because paths
  move; a single corpus with overlays avoids that class of bug.
- **Always-inject-everything.** Budget per turn is a design feature, not a limit
  to work around.

## Suggested order

1. Write path (tools) — highest impact per hour.
2. Pending capture + review — closes the real gap safely.
3. Consolidation — keeps the corpus honest as it grows.
4. Search tool, then optional answers-only embeddings.
5. Project overlays, provenance, staleness.
6. Cache-aware injection once the corpus is stable enough to hash.
