# Personal Memory Checklist

The detailed plan is in [plan.md](plan.md). The initial product comparison is in [existing-solutions-comparison.md](../research/existing-solutions-comparison.md). The user approved building our own core where existing solutions do not meet the requirements.

## Preparation

- [x] Confirm the repository and existing specification.
- [x] Compare documented existing products and record requirement gaps.
- [x] User confirmed custom development if no complete solution exists; reuse UI/adapters where useful.

## Phase 0 — Evaluate Existing Products

- [x] Compare Khoj, Open WebUI, AnythingLLM, Memos, Mem0, and Letta against priority requirements.
- [ ] Manually prototype with synthetic data for the most suitable candidates.
- [x] Recommend an interoperable custom core; evaluate existing products as UIs/clients/adapters.
- [x] User approved the custom direction on 2026-10-01.

## Phase 1 — Foundation and Contracts

- [ ] Inspect the available runtime and repository instructions.
- [ ] Define RAW / INDEX / DERIVED contracts and RAW preservation rules.
- [ ] Define the initial schema and versioned migrations, including attachment binary metadata, hashes, and source links.
- [ ] Document local initialization and backup.
- [ ] Manual acceptance review.

## Phase 2 — API and Lexical Search

- [ ] Versioned local API.
- [ ] FTS5 index and provenance in results.
- [ ] Documented generic import without assumptions about the ChatGPT export.
- [ ] Manual walkthrough with synthetic data.

## Phase 3 — ChatGPT Import (when the archive is available)

- [ ] Inspect the archive and inventory its real formats.
- [ ] Implement an adapter based on the observed format.
- [ ] Preserve RAW and ensure retryable import with a results report, including attached images/files and their source-message links.
- [ ] Verify locally and privately using a copy of the archive; do not put data or results in Git.

## Phase 4 — UI and Android on LAN

- [ ] Search, exploration, and provenance UI.
- [ ] Entity and relationship map.
- [ ] Image/file previews, original access, and offline access to synced attachments on Android.
- [ ] Local Android access and a message for when the PC is unavailable.
- [ ] Manual PC + Android walkthrough.

## Phase 5 — Semantic Search

- [ ] Replaceable embeddings provider and version metadata.
- [ ] Integrate local models Qwen, gpt-oss-20b, and Gemma 4 through compatible runtimes.
- [ ] Combined FTS + semantic search.
- [ ] Manual walkthrough or documentation of missing local dependencies.

## Phase 6 — MCP and Adapters

- [ ] Initially read-only MCP bridge.
- [ ] Adapters for ChatGPT and the OpenCode and Hermes agent harnesses.
- [ ] Validation and logging before any write operation.
- [ ] Manual connection in each supported client.

## Phase 7 — Synchronization and Recovery

- [ ] Design PC-authoritative replication and conflict handling.
- [ ] Document LAN access and backup/restore.
- [ ] Manual restoration walkthrough.
