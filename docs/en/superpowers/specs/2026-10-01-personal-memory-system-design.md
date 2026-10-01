# Personal Memory System Design

**Status:** Direction confirmed by the user on 2026-10-01  
**Date:** 2026-10-01

## Goal

Incrementally build a personal memory system accessible from Windows and Android. The PC hosts the services and primary copy; the phone keeps a local, searchable-offline copy that syncs with the PC when both are on the same Wi-Fi network. Remote access may be added later through a private network such as Tailscale.

The system preserves sources intact, shows the provenance of each piece of information, and can later serve local Qwen, OpenCode, and Hermes. ChatGPT integration is a separate, optional target. As of 2026-10-01, OpenAI documentation says MCP apps are web-only, not mobile; ChatGPT connects to remote MCP servers, and a server on a private network may need a Secure MCP Tunnel. Access and available actions depend on plan/client. The purpose-built Android app remains the direct mobile route. [OpenAI source](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

Full requirements, scenarios, acceptance criteria, and portfolio rationale are in the [requirements document](../../project/requirements-and-scope.md). The product comparison is in the [existing-solutions evaluation](../../research/existing-solutions-comparison.md).

## Proposed Architecture

- **Windows host:** local service with primary database, versioned API, and search. It listens only on the configured local network; access requires pairing/authorization for the phone. No router port forwarding by default.
- **Android:** installable app with a local database/cache for offline search and a sync queue. Choose the first client—installable PWA or native app—after checking offline needs and the available environment.
- **Synchronization:** the protocol transfers identified changes with versions and provenance between phone and PC. Conflicting changes are not silently overwritten; both variants are preserved and marked for resolution.
- **AI clients:** the API is the shared contract for apps. A separate MCP adapter initially exposes limited search/read operations and later controlled writes. Enable ChatGPT integration only on surfaces/plans that support it.

## Data Separation

- **RAW:** original imported files, preserved byte-for-byte and identified by hash. No normalization or editing modifies them.
- **INDEX:** normalized data for search and synchronization, with references to originating RAW files and records.
- **DERIVED:** extracted text, chunks, embeddings, entities, relationships, summaries, and inferred claims. These can be rebuilt or marked reviewed without modifying RAW.

The source-of-truth schema will include sources and imports, conversations/documents, messages, attachments, people/entities, claims and relationships, provenance, search passages, and sync events. Extracted facts link to the exact source and passage supporting them, and retain their state (derived, verified, or disputed).

## ChatGPT Import Without Assumptions

Do not encode an anticipated export format. The importer has an adapter interface and a staged workflow: inspect the real archive (file list and observed structure), report its contents, map observed formats to a canonical model, then perform an idempotent import. Copy the original archive into RAW before processing. Unknown items are reported and preserved, not discarded. Import does not begin until the user provides the archive and its format has been inspected.

## Search and Knowledge Graph

The first search phase uses full-text and filters by source, date, and entity. Semantic search uses locally generated embeddings through a configurable model adapter; the vector index is derived and rebuildable. The knowledge graph stores entities, relationships, and claims together with provenance. Automatic extraction is not treated as a verified fact without confirmation.

## Interface

The Windows/Android interface provides search, sourced results, conversation/document views, entity and relationship exploration, sync status, and provenance inspection. Editing and claim verification are explicit actions. Android uses the same API and provenance conventions as AI services.

## Incremental Delivery

1. **Data contract and local core:** schema, migrations, RAW/INDEX/DERIVED directories, provenance, and Windows configuration.
2. **Search and API:** full-text search, versioned endpoints, and shared client contract.
3. **Android client and LAN sync:** local cache, pairing, synchronization, and offline search.
4. **Exploration and graph:** search/map interface and provenance-aware claims.
5. **AI adapters:** MCP for local clients, local embeddings, and ChatGPT integration where supported.
6. **ChatGPT import:** after the archive arrives, inspect it and implement an appropriate adapter.

Each slice remains usable and additive. Imports, indexes, and derived data must be rebuildable without losing the raw source.

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
