# Personal Memory: Requirements, Scope, and Project Rationale

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** The user has confirmed the direction to build our own system where existing products do not meet the requirements; delivery is incremental.  
**Related documents:** [System design](../superpowers/specs/2026-10-01-personal-memory-system-design.md), [Existing-solutions comparison](../research/existing-solutions-comparison.md), [Implementation plan](../tasks/plan.md), [Checklist](../tasks/todo.md).

## 1. Summary

Personal Memory is a local-first personal system that brings conversations and other sources into a repository controlled by the user. The repository must remain useful independently of the AI provider or interface: ChatGPT, a local model such as Qwen, OpenCode, Hermes, or a purpose-built interface.

The system preserves original sources separately from normalized content, indexes, and generated knowledge. It supports full-text and semantic search, navigation through conversations and relationships, and tracing every result back to its source. It is accessible from a Windows PC and Android. The PC is planned as the host and primary source of truth; the phone may hold a local copy or cache for offline use and later synchronization over the home network.

This is also a portfolio project. It documents a real need, evaluated alternatives, tradeoffs, data modeling, robust import, provenance, search, and integration with multiple AI clients. The goal is not to claim that a custom product is superior in every situation, but to show which concrete requirements remain unmet by existing solutions and how this system addresses them.

## 2. Problem and User Context

Useful history is scattered across conversations and tools. The built-in memory of one assistant does not give the user an independent repository that is easy to audit, export, and reuse with another agent. Basic search is insufficient when the user remembers the idea but not the exact wording; summaries without sources can distort context; and connecting to a home PC must account for the LAN and phone usage.

The user works on Windows, keeps projects under `D:\AI`, uses Android, and is usually at home with the phone and PC on the same network. The project has a GitHub repository: [victorarsenie/PersonalMemory](https://github.com/victorarsenie/PersonalMemory). A ChatGPT export archive has been requested and may arrive later. Its format is not yet available for inspection.

## 3. Goals

1. A user-controlled memory repository, with a canonical copy on the PC.
2. Byte-for-byte preservation of imported source files, with hashes and metadata.
3. Regenerable indexes and derived data, each linked to the source that supports it.
4. Lexical and semantic search, with filters and citable results.
5. Exploration of conversations, documents, entities, and relationships in a graph view.
6. Use from Windows and Android; LAN access in the first phase and phone offline support to the extent established by prototyping.
7. An API and adapters that let different applications and agents use the same repository.
8. ChatGPT import without assumptions about the export schema; implement the parser only after receiving and inspecting the real archive.
9. Document the project's differentiation from existing products and present implemented capabilities honestly in the portfolio.

## 4. Non-goals and Boundaries

- We are not rebuilding a language model or replacing ChatGPT, Qwen, OpenCode, or Hermes.
- We do not assume MCP integration is available in every ChatGPT app; verify the specific transport, plan, and client when integration work begins.
- We do not invent the ChatGPT export structure before inspecting it.
- We do not modify original archives or automatically promote extracted content to verified facts.
- We do not expose the PC directly to the internet or open router ports by default.
- We do not enable bidirectional synchronization without identifiers, versions, a journal, and explicit conflict handling.
- We do not build a native Android app immediately if an installable web client meets measured requirements; choose after prototyping.
- Core local search must not depend on a cloud service.

## 5. Users and Scenarios

### 5.1 Repository owner

- Adds or imports a source and reviews the ingestion report.
- Searches by words, concepts, time range, provenance, or entity.
- Opens a citation in the context of its original message or document.
- Reviews, confirms, or corrects derived entities and relationships.
- Uses the system from a phone on the same network; when the PC is unavailable, consults the available local copy and syncs later.
- Backs up the repository and can rebuild INDEX/DERIVED from RAW.

### 5.2 AI agent or external client

- Searches the personal repository through a stable API or MCP.
- Receives relevant passages with metadata and provenance, not unsupported assertions.
- Initially reads data only; any write operation requires explicit authorization and logging rules.

### 5.3 Later ChatGPT export import

- The user provides the archive.
- The system inventories files and identifies the actual structure without deleting or rewriting the source.
- The importer reports recognized, skipped, or unknown files and maps confirmed data to the canonical model.
- Retrying an import does not duplicate content; errors are explainable and recoverable.

## 6. Functional Requirements

### F-01 — Sources and Imports

Each ingestion has an identifier, source type, import time, adapter version, and outcome. Sources may be archives, documents, or later imports. An import preserves originals, describes what it processed, and can be retried without creating duplicates.

### F-02 — Data Separation

- **RAW:** original received files, read-only after ingestion, with SHA-256 hashes and minimal metadata; preserved byte-for-byte.
- **INDEX:** normalized canonical model, content for listing/search, and regenerable lexical/vector indexes.
- **DERIVED:** passages, extracts, summaries, embeddings, entities, relationships, and claims. Each derived item records method/model, version, time, and relevant source/passage.

Reindexing may delete and rebuild only regenerable structures; it must not alter RAW.

### F-03 — Provenance and Audit

Every result or claim must point to the source, conversation/document, message/passage, and position where the format allows. Distinguish original content, automatically extracted content, user-confirmed content, and disputed/corrected content. Preserve transformation and synchronization history.

### F-04 — Search

Lexical search supports phrases and filters by date, source, conversation, entity, and type. Semantic search uses embeddings through a configurable provider, preferably local, and can be rebuilt when the model changes. Combined results show relevant passages, useful scores, metadata, and links to full context.

### F-05 — Knowledge Graph

The graph stores entities, relationships, and claims as derived data with provenance. The interface lets users navigate from a concept to the conversations and passages that support it. Automatically extracted content remains marked as such until confirmed; contradictions are not silently overwritten.

### F-06 — API and MCP

The versioned API is the shared contract for the UI and integrations. MCP initially exposes search and read operations; every result includes provenance. Agent writes are enabled separately after approval, validation, and change-log rules are defined. Adapters for ChatGPT, Qwen, OpenCode, and Hermes are optional components and do not change the data model.

**ChatGPT limitation:** OpenAI's official documentation checked on 2026-10-01 says MCP apps are available on web, not mobile; ChatGPT connects to remote MCP servers, not directly to a local server. A server on a private network needs a Secure MCP Tunnel for supported OpenAI products. Developer mode and full MCP actions depend on plan and workspace. Therefore, a purpose-built Android UI/API remains necessary; ChatGPT integration is an optional web route, not the only mobile interface. [OpenAI: Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

### F-07 — PC, Android, and Synchronization

The PC hosts the service and primary copy. Android connects on the LAN and may hold a local replica/cache. Synchronization transfers identified/versioned changes and detects conflicts without losing variants. Choose the exact protocol and PWA versus native client after prototyping and validating offline requirements.

### F-08 — Interface

The interface provides search, result lists, conversation/document views with passage navigation, an entity/relationship map, provenance inspection, synchronization status, and an import flow. It must make the distinction between source and inference visible.

### F-09 — Backup, Privacy, and Portability

Backups include RAW, the canonical database, and the configuration needed for restoration; regenerable indexes may be rebuilt. LAN access is authorized; public ports are not exposed by default. Export formats and schema are documented so the user is not locked into one client.

## 7. Non-functional Requirements

- **Local-first:** core storage and search run on the user's devices; cloud connectivity is not required for core functions.
- **Source safety:** operations on INDEX/DERIVED do not alter RAW files.
- **Traceability:** results and relationships are explainable through provenance.
- **Interoperability:** AI clients can change without migrating the canonical repository into a proprietary memory service.
- **Reproducibility:** migrations and initialization/import operations are versioned and documented.
- **Incremental evolution:** each phase produces a usable slice with stable contracts and clear migration.
- **Portability:** schema and exports are documented sufficiently for backup, audit, and migration.

## 8. Architecture and Principles

### 8.1 Components

1. **Local data store:** RAW files and canonical database on the PC.
2. **Ingestion/import adapters:** parse known sources and report unknowns.
3. **Search/index service:** full-text and later semantic indexes.
4. **Versioned local API:** used by the UI, phone, and clients.
5. **Exploration UI:** initially a browser/installable web app; validate PWA versus native separately.
6. **Android replica/sync:** incremental feature with offline cache and explicit conflict resolution.
7. **AI adapters:** MCP, embeddings, and client-specific integrations isolated from the core.

### 8.2 Initial Domain Model

Candidate entities: `Source`, `ImportRun`, `Conversation`, `Message`, `Attachment`, `Document`, `Passage`, `Entity`, `Claim`, `Relation`, `Provenance`, `Embedding`, `SyncEvent`, and `Revision`. Exact identifiers, schema, and states are set in an architecture decision before implementing the core.

### 8.3 Design Principles

- The source of truth resides in the user's repository, not an assistant's index.
- RAW is not a cache and cannot be recreated from normalized data.
- INDEX and DERIVED are rebuilt with explicit parser/model versions.
- Relationships and derived memories retain the citations that support them.
- Interfaces are adapters; data contracts are independent of them.
- Choose technologies based on the user's Windows environment and document dependencies, not just familiarity.

## 9. Existing Products and Rationale for Building

Products evaluated include Khoj, Open WebUI, AnythingLLM, Memos, Mem0, and Letta. They provide useful capabilities for personal knowledge management, RAG, agent memory, graph memory, or MCP; the project should not automatically reimplement their UI or runtime.

The [comparison document](../research/existing-solutions-comparison.md) links to official documentation and phrases gaps as “not identified in the reviewed documentation.” The working hypothesis is that none of the documented products combines, in one user-controlled repository: RAW preservation of the real archive, ChatGPT import adapted after inspection, granular provenance, rebuildable indexes, an explorable graph, hybrid search, and interoperability across PC/Android/agents.

Therefore the approved direction is **to build the core that addresses these gaps and reuse existing products when doing so reduces effort without compromising data ownership and provenance**. If prototyping shows an alternative covers more than expected, reduce the custom scope. Revisit this decision based on evidence, not attachment to custom implementation.

## 10. Portfolio Value and Presentation

The project can demonstrate:

- problem analysis and evaluation of alternatives;
- local-first architecture with clear RAW/INDEX/DERIVED responsibilities;
- a resilient, idempotent, explainable ingestion pipeline;
- provenance and graph/data modeling;
- lexical and semantic search with local models;
- API/MCP and multi-agent integration;
- PC/Android access, LAN, offline sync, and conflict handling;
- privacy, backup, and portability decisions;
- incremental delivery and technical documentation.

The portfolio should show a demo using synthetic or authorized data, architecture, alternatives, decisions, screenshots, and limitations. It must not publish personal conversations, real archives, credentials, or results that expose private data. Do not claim a feature is complete until there is a verifiable demonstration.

## 11. Delivery Phases and Acceptance Criteria

### Phase 0 — Evaluate and Prototype Existing Products

- Complete the documented evaluation and practically check the closest candidates using synthetic data.
- Decide whether an existing product becomes the UI/client, whether to extend a product, or whether the custom core remains justified.
- Acceptance: a criteria-based decision with observed gaps; involve the user when scope changes materially.

### Phase 1 — Data Foundation

- Establish repository instructions, runtime, RAW/INDEX/DERIVED layout, Git-ignored configuration, database, and migrations.
- Acceptance: an empty repository can be initialized; schema is versioned; reindexing demonstrably leaves RAW unchanged.

### Phase 2 — API and Lexical Search

- Versioned API, controlled source/import operations, FTS, and results with provenance.
- Acceptance: synthetic content can be added, searched, and opened in its source context.

### Phase 3 — ChatGPT Importer

- After the archive arrives, inventory the real formats; preserve the raw archive and implement adapters for observed formats.
- Acceptance: complete report, retryable import, unknowns preserved/reported, verifiable provenance.

### Phase 4 — PC/Android UI and Graph

- Search, context, provenance, graph exploration, LAN access, and incremental cache/sync.
- Acceptance: demonstrated use on PC and Android; conflicts do not disappear without notice.

### Phase 5 — Semantic Search and Local Models

- Configurable local embedding provider, model/version metadata, lexical/semantic fusion.
- Acceptance: semantic results point to identifiable passages; re-embedding does not alter RAW.

### Phase 6 — MCP and Clients

- Initially read-only MCP; test each target client and document transport restrictions.
- Acceptance: search/read returns sources and provenance; writes remain disabled until explicitly authorized.

### Phase 7 — Backup, Security, and Hardening

- Backup/restore procedure, LAN authorization, logs, and optional remote access through a private network.
- Acceptance: restoration is demonstrated; no default public exposure.

## 12. Risks and Questions to Validate

- **Unknown export format:** defer the parser until the real archive; start with the adapter interface and contract.
- **Different MCP support per client:** test at integration time; ChatGPT MCP apps are web-only and do not connect directly to a local server according to reviewed OpenAI documentation. Keep a separate Android client; consider a private tunnel only for supported OpenAI surfaces.
- **Offline and replication complexity:** prototype and measure before choosing PWA/native and a sync protocol.
- **Inaccurate inferences:** use verification states and citations; the user retains control of facts.
- **Scope growth:** deliver phases with acceptance criteria and reuse existing products where central requirements are preserved.
- **Local model availability:** the core works with lexical search without embeddings; configure semantic search later.

## 13. Decision History

- **2026-10-01:** The user confirmed Windows PC and Android as target devices, usually on the same home network, the repository under `D:\AI\PersonalMemory`, GitHub for versioning, a later ChatGPT archive, and future integration with Qwen/OpenCode/Hermes.
- **2026-10-01:** The user confirmed building our own system if existing products do not meet the requirements, and requested documenting the comparison and added value as a portfolio project.
- **2026-10-01:** OpenAI documentation confirms MCP apps are web-only, connect to remote servers, and may require a Secure MCP Tunnel for private-network servers; direct mobile MCP access is not assumed.
- The ChatGPT export has not been inspected; its schema remains unknown.
