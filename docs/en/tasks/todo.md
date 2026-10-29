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

## Phase 3 — ChatGPT Import

- [x] Inspect the local archive and inventory its real formats without publishing content.
- [x] Create an entirely synthetic demo package and Git rules that exclude personal exports.
- [ ] Import the entire archive as historical backfill: all included conversations and messages, in the observed order and structure, without reducing them to summaries.
- [ ] Implement and review the modular adapter for the observed format; retain unknown payloads and content parts linked to RAW.
- [ ] Preserve RAW and ensure retryable import with a coverage report for processed/skipped/unknown messages and attachments.
- [ ] Verify locally and privately using a copy of the archive; do not put data or results in Git.

## Phase 4 — Current Capture, UI, and Android on LAN

- [ ] Periodic detailed structured checkpoint for the active ChatGPT conversation since the previous capture; preserve accessible raw transcript in RAW and report method, interval, coverage, and gaps.
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

- [ ] Design bidirectional replication between two complete local databases and conflict handling.
- [ ] Document LAN access and backup/restore.
- [ ] Manual restoration walkthrough.
