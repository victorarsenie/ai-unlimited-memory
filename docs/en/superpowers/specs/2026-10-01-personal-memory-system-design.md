# Personal Memory System Design

**Status:** Direction confirmed by the user on 2026-10-01  
**Date:** 2026-10-01

## Goal

**The central objective is preserving useful conversation context over time.** Import the historical ChatGPT archive in full as backfill. For current and future conversations, save detailed, structured periodic checkpoints; these may compress repetition while retaining decisions/rationale, facts, preferences/corrections, actions/status/deadlines, open questions, changes, and source links. A checkpoint is derived, not a verbatim transcript. Preserve accessible raw transcripts intact in RAW. Show and validate capture method and coverage.

Incrementally build a personal memory system accessible from Windows and Android. The Windows and Android apps each keep a complete local copy. They synchronize changes bidirectionally on the same local network or when the user requests it; each can search and read local data while the other device is offline. Remote access may be added later through a private network such as Tailscale.

The system preserves sources intact, including images and attached files, shows the provenance of each piece of information, and can later serve local models such as Qwen, gpt-oss-20b, and Gemma 4, as well as agent harnesses such as OpenCode and Hermes. ChatGPT integration is a separate, optional target. As of 2026-10-01, OpenAI documentation says MCP apps are web-only, not mobile; ChatGPT connects to remote MCP servers, and a server on a private network may need a Secure MCP Tunnel. Access and available actions depend on plan/client. The purpose-built Android app remains the direct mobile route. [OpenAI source](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

Full requirements, scenarios, acceptance criteria, and portfolio rationale are in the [requirements document](../../project/requirements-and-scope.md). The product comparison is in the [existing-solutions evaluation](../../research/existing-solutions-comparison.md).

## Proposed Architecture

- **Windows app:** keeps a complete local database and exposes a local API for sync/search; the service listens only on the configured local network, and paired devices are authorized. No router port forwarding by default.
- **Android:** installable app with a complete local database, Share-based capture, and an offline sync queue. Distribution is planned through Google Play after testing and review.
- **Synchronization:** the protocol transfers identified changes with versions and provenance between two complete replicas. Conflicting changes are not silently overwritten; both variants are preserved and marked for resolution.
- **AI clients:** the API is the shared contract for apps. A separate MCP adapter initially exposes limited search/read operations and later controlled writes. Enable ChatGPT integration only on surfaces/plans that support it.

## Data Separation

- **RAW:** original archives and imported binaries, including images and attachments, preserved byte-for-byte and identified by hash. No normalization or editing modifies them.
- **INDEX:** normalized data for search and synchronization, with references to originating RAW files and records.
- **DERIVED:** extracted text, thumbnails, OCR, chunks, embeddings, entities, relationships, summaries, and inferred claims. These can be rebuilt or marked reviewed without modifying RAW; visual processing is optional and preferably local.

The initial canonical schema uses SQLite and versioned SQL migrations, as recorded in [ADR-0001](../../decisions/0001-sqlite-local-data-foundation.md). Migrations 001/002 model sources/imports, coverage-aware capture records, conversations, messages/branches, multimodal parts, raw objects and attachments, documents, entities, claims, relations, and provenance. Search passages and synchronization events are added in their respective phases. Extracted facts link to their supporting source and retain a state (derived, confirmed, or contested).

## GitHub and Personal-Data Boundary

The GitHub repository and portfolio use synthetic data only. The user’s real conversations and ChatGPT archive are used only in the local Personal Memory instance. Keep RAW, INDEX, DERIVED, backups, ingestion logs, and outputs derived from private data outside tracked Git content. Configure exclusions before importing the real archive. Generate synthetic demo data independently rather than anonymizing the user’s conversations. Importer validation against a copy of the actual archive may happen locally; its content and outputs are not published.

## ChatGPT Historical Backfill and Ongoing Capture

Archive import is necessary for recovering existing history: when available, inspect the real format, preserve the original ZIP in RAW, and import all conversations, messages, and content parts present. The importer makes no schema assumptions before inspection; retain branches/variants and unknown payloads through locators to RAW, and report coverage, errors, and uninterpreted items. Deleted conversations or content absent from the export cannot be reconstructed.

Beyond archive backfill, current and later conversations should be saved as periodic detailed, structured checkpoints. An explicit checkpoint is acceptable where automatic capture is unavailable. Validate each method and show uncaptured intervals/parts. Accessible raw transcripts remain in RAW; summaries are derived, provenance-linked, and not labeled as transcripts. OpenAI’s documented ChatGPT export is user-requested and delivered as a ZIP; the documentation reviewed here does not describe automatic per-message sync to a local repository.

## Search and Knowledge Graph

The first search phase uses full-text and filters by source, date, and entity. Semantic search uses locally generated embeddings through a configurable model adapter; the vector index is derived and rebuildable. The knowledge graph stores entities, relationships, and claims together with provenance. Automatic extraction is not treated as a verified fact without confirmation.

## Interface

The Windows/Android interface provides explicit capture and a report for the current ChatGPT conversation, search, sourced results, conversation/document and attached image/file views, entity and relationship exploration, sync status, and provenance inspection. Editing and claim verification are explicit actions. Android uses the same API and provenance conventions as AI services.

## Incremental Delivery

1. **Data contract and local core:** schema, migrations, RAW/INDEX/DERIVED directories, and provenance.
2. **ChatGPT historical backfill:** the received archive has been inspected locally; import all conversations/messages/parts present and report coverage and uninterpreted items, then report coverage and uninterpreted items.
3. **API and search:** navigate/search complete transcripts, linked to their message and location in the RAW archive.
4. **Current capture and Android client:** provide a flow to save the active conversation transcript and later conversations; validate the method and report gaps. Sync transcripts and attachments to the offline Android copy.
5. **Exploration and graph:** extract derived data with provenance without replacing conversations.
6. **AI adapters:** MCP, local embeddings, and ChatGPT integration where supported.
## Out of Scope for the First Version

- Public access to the PC, open router ports, or sync through a third-party cloud.
- Assumptions about the ChatGPT archive structure.
- Automatically promoting summaries/entities to verified facts.
- Agent writes without provenance and explicit authorization rules.

## Foundation Acceptance Criteria

- A source can be preserved in RAW and traced through its hash and provenance metadata.
- Indexes and DERIVED data can be rebuilt without modifying RAW.
- The canonical model and API do not depend on one export format or one AI model.
- The architecture clearly distinguishes the primary PC copy, Android replica, and sync conflicts.
- ChatGPT mobile is not presented as connected over MCP while that feature is unsupported.
- The current conversation can be saved as a detailed structured checkpoint for the interval since the previous capture; the report identifies method, coverage, and missing parts. Preserve any accessible raw transcript in RAW.
