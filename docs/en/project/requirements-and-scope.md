# Personal Memory: Requirements, Scope, and Project Rationale

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** The user has confirmed the direction to build our own system where existing products do not meet the requirements; delivery is incremental.  
**Related documents:** [System design](../superpowers/specs/2026-10-01-personal-memory-system-design.md), [Existing-solutions comparison](../research/existing-solutions-comparison.md), [Implementation plan](../tasks/plan.md), [Checklist](../tasks/todo.md).

## 1. Summary

**The primary goal is to preserve useful conversation context over time.** Import the historical ChatGPT archive in full and keep its original intact in RAW. For current and future conversations, the system may save checkpoints as detailed, structured summaries that remove repetition while retaining decisions, preferences, facts, corrections, actions, open questions, and temporal context. When a source transcript is accessible, preserve it intact in RAW; the derived summary links to its conversation and source messages. A summary is never labeled as a verbatim transcript.

Personal Memory is a local-first personal system that brings conversations and other sources into a repository controlled by the user. The repository must remain useful independently of the AI provider or interface: ChatGPT, local models such as Qwen, gpt-oss-20b, and Gemma 4, agent harnesses such as OpenCode and Hermes, or a purpose-built interface.

The system preserves original sources separately from normalized content, indexes, and generated knowledge. It supports full-text and semantic search, navigation through conversations and relationships, and tracing every result back to its source. It is accessible from a Windows PC and Android. Windows and Android each keep a complete local database. The apps synchronize bidirectionally over the local network or when the user requests it; each device can work independently offline.

This is also a portfolio project. It documents a real need, evaluated alternatives, tradeoffs, data modeling, robust import, provenance, search, and integration with multiple AI clients. The goal is not to claim that a custom product is superior in every situation, but to show which concrete requirements remain unmet by existing solutions and how this system addresses them.

## 2. Problem and User Context

Useful history is scattered across conversations and tools. The built-in memory of one assistant does not give the user an independent repository that is easy to audit, export, and reuse with another agent. Basic search is insufficient when the user remembers the idea but not the exact wording; summaries without sources can distort context; and connecting to a home PC must account for the LAN and phone usage.

The user works on Windows, keeps projects under `D:\AI`, uses Android, and is usually at home with the phone and PC on the same network. The project has a GitHub repository: [victorarsenie/PersonalMemory](https://github.com/victorarsenie/PersonalMemory). The ChatGPT export archive has been received and inspected locally; the importer targets the observed structure, and the real archive stays outside the Git repository.

## 3. Goals

1. A user-controlled dataset with equivalent complete local copies on Windows and Android and every available message in source order.
2. Importing the ChatGPT archive is the required historical backfill: import every conversation present in the supplied archive without reducing it to summaries or extracted facts.
3. Preserve the archive and raw files byte-for-byte, with hashes and metadata.
4. Capture new conversations through a separately validated method; show conversations or portions that were not captured.
5. Keep regenerable indexes and derived data linked to their supporting transcript; summaries and the knowledge graph never replace the conversation.
6. Provide lexical and semantic search with filters and citable results.
7. Explore conversations, documents, entities, and relationships in a graph view.
8. Support Windows and Android, LAN access initially, and phone offline use as established by prototyping.
9. Provide an API and adapters so different applications and agents can use the same repository.
10. Include attached images and files, preserve originals, retain source-message links, and make them accessible on PC/Android.
11. Document differentiation from existing products and present implemented capabilities honestly in the portfolio.

## 4. Non-goals and Boundaries

- We are not rebuilding a language model or replacing ChatGPT, local models Qwen, gpt-oss-20b, and Gemma 4, or the OpenCode and Hermes agent harnesses.
- We do not assume MCP integration is available in every ChatGPT app; verify the specific transport, plan, and client when integration work begins.
- We do not invent the ChatGPT export structure before inspecting it.
- We do not modify original archives or automatically promote extracted content to verified facts.
- We do not expose the PC directly to the internet or open router ports by default.
- We do not enable bidirectional synchronization without identifiers, versions, a journal, and explicit conflict handling.
- We do not build a native Android app immediately if an installable web client meets measured requirements; choose after prototyping.
- Core local search must not depend on a cloud service.

## 5. Users and Scenarios

### 5.1 Repository owner

- Periodically saves a detailed, structured checkpoint of the current conversation since the previous capture and reviews its coverage; can also preserve the raw transcript when accessible.
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

### 5.3 ChatGPT History Recovery and Conversation Capture

- Archive import is required for historical backfill: ingest every conversation included in the supplied export and preserve the original archive in RAW.
- Preserve messages across roles and their observed order/structure, including variants and multimodal parts present in the export.
- The import report lists conversations and messages found, imported, skipped, or not interpretable; unknown payloads remain in RAW and are marked unprocessed.
- An archive cannot recover deleted conversations or content absent from the export. Do not claim complete history without stating archive coverage and errors.
- In addition to archive backfill, active and later conversations can be preserved through structured checkpoints at intervals or before compaction. Retain important content and source links, remove repetition, and show the capture method and gaps.

## 6. Functional Requirements

### F-01 — Conversation Archiving and Source Ingestion

For historical archive imports, preserve every available message, role/author, order, timestamp, variant/branch, and source-provided content part; retain unknown content as an opaque payload linked to RAW. For current/future captures, the system may create detailed structured summaries for the interval since the prior checkpoint: important context/facts, preferences and corrections, decisions with rationale, actions with status/deadline, unresolved questions, and links to messages/attachments. Repetition can be compressed; contradictions and changes over time must remain visible. Keep an accessible raw transcript intact in RAW; the summary is derived, versioned, and labeled as a summary rather than a transcript.

Each capture/import records method, time, interval, saved representation (transcript, structured summary, or both), coverage (complete/partial/unknown), and a report of processed, skipped, and failed items. For Codex, a PreCompact hook can provide the transcript path before compaction when available; because its format is not a stable interface, archive the raw copy in RAW before interpreting it. Captures are retryable without duplicates.

### F-02 — Data Separation

- **RAW:** source archives and original image/file binaries, read-only after ingestion, preserved byte-for-byte and identified by SHA-256.
- **INDEX:** canonical structure of every conversation and message, order, role, content parts, variants, source locators, and attachment metadata. Lexical/vector indexes are rebuildable; the normalized transcript is never replaced by summaries.
- **DERIVED:** passages, extracted text, thumbnails, OCR, embeddings, summaries, entities, relationships, and claims. Each derived result retains provenance and processor/model version.

Reindexing may delete and rebuild only regenerable structures; it must not alter RAW.

### F-03 — Provenance and Audit

Every result or claim must point to the RAW archive, conversation, message/variant, content part, and source position where available. Provenance also links each imported transcript back to its original file. Distinguish original content, automatically extracted content, user-confirmed content, and disputed/corrected content. Preserve transformation and synchronization history.

### F-04 — Search

Lexical search supports phrases and filters by date, source, conversation, entity, and type. Semantic search uses embeddings through a configurable provider, preferably local, and can be rebuilt when the model changes. Combined results show relevant passages, useful scores, metadata, and links to full context.

### F-05 — Knowledge Graph

The graph stores entities, relationships, and claims as derived data with provenance. The interface lets users navigate from a concept to the conversations and passages that support it. Automatically extracted content remains marked as such until confirmed; contradictions are not silently overwritten.

### F-06 — API and MCP

The versioned API is the shared contract for the UI and integrations. MCP initially exposes search and read operations; every result includes provenance. Agent writes are enabled separately after approval, validation, and change-log rules are defined. Adapters for local models Qwen, gpt-oss-20b, and Gemma 4, plus ChatGPT, OpenCode, and Hermes clients/agents, are optional components and do not change the data model.

**ChatGPT limitation:** OpenAI's official documentation checked on 2026-10-01 says MCP apps are available on web, not mobile; ChatGPT connects to remote MCP servers, not directly to a local server. A server on a private network needs a Secure MCP Tunnel for supported OpenAI products. Developer mode and full MCP actions depend on plan and workspace. Therefore, a purpose-built Android UI/API remains necessary; ChatGPT integration is an optional web route, not the only mobile interface. [OpenAI: Developer mode and MCP apps in ChatGPT](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

### F-07 — PC, Android, and Synchronization

The PC hosts the service and primary copy. Android connects on the LAN and may hold a local replica/cache, including synced attachments for offline access. Synchronization transfers identified/versioned changes and files, can resume interrupted transfers, and detects conflicts without losing variants. Choose the exact protocol and PWA versus native client after prototyping and validating offline requirements.

### F-08 — Interface

The interface provides search, result lists, conversation/document views with passage navigation, an entity/relationship map, provenance inspection, synchronization status, and an import flow. It previews supported images/files in source context and provides access to originals. It must make the distinction between source and inference visible.

### F-10 — Images and File Attachments

The system imports and preserves image/file attachments from conversations and documents, including formats without an available extractor. Keep each original intact in RAW and record its hash, name, observed MIME type, size, and provenance to the source/originating message where available. The attachment remains accessible from its conversation context on PC and Android; the interface can display images or supported previews and open/download the original.

Extract and index content only for formats supported by configured processors. For images, OCR, visual description, and visual embeddings are optional derived capabilities, preferably processed locally. Unknown or unreadable files must not block import: preserve and link them to their source, and make them discoverable by name/metadata. Thumbnails, OCR, and extracted text are rebuildable and never replace originals. Transfer files to the Android replica with resumable transfers and offline access to synced items.

Acceptance: the original can be opened/recovered with an identical hash after import; the attachment has a navigable source link; supported content is searchable; unknown types are preserved and reported.

### F-09 — Backup, Privacy, and Portability

Backups include RAW, the canonical database, and the configuration needed for restoration; regenerable indexes may be rebuilt. LAN access is authorized; public ports are not exposed by default. Export formats and schema are documented so the user is not locked into one client.

### F-11 — Historical Backfill and Capture Coverage

Importing the ChatGPT archive is the required path for recovering historical conversations still present in the export. Separately, the system must save the current and later conversations as detailed, structured checkpoints with source and attachment links; when the raw transcript is accessible, preserve it in RAW. Until that method is validated, the interface shows which sources and time ranges are not captured. Do not claim automatic or exhaustive capture without evidence and a coverage report. OpenAI’s documented export is user-initiated in settings and delivers a ZIP; the documentation reviewed here does not describe automatic per-message sync to a local repository. [ChatGPT Android data export](https://help.openai.com/en/articles/8167885-how-to-export-your-data-from-the-chatgpt-android-app).

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
- lexical and semantic search with local models such as Qwen, gpt-oss-20b, and Gemma 4;
- API/MCP and multi-agent integration;
- PC/Android access, LAN, offline sync, and conflict handling;
- privacy, backup, and portability decisions;
- incremental delivery and technical documentation.

Demos, screenshots, fixtures, and all data in the GitHub repository use synthetic data only. The user’s real conversations and archive are used only locally in the Personal Memory instance. Never publish or commit archives, RAW, extracts, indexes, embeddings, logs, screenshots, or results containing personal data. Do not claim a feature is complete until there is a verifiable demonstration.

## GitHub and Local-Use Data Policy

- The GitHub repository, including commits and portfolio materials, contains only code, documentation, and synthetic data created specifically for demonstrations.
- Synthetic data is not produced by anonymizing real conversations; generate it separately to avoid leaks through details or metadata.
- The ChatGPT archive and personal conversations are imported only into the user-configured local instance. Never copy them into Git-tracked directories.
- RAW, INDEX, DERIVED, backups, ingestion logs, and artifacts generated from personal sources stay local and are excluded from Git. Configure the repository to enforce this before importing real data.
- Prototypes, walkthroughs, and public materials use synthetic data. Importer correctness may also be checked locally against a copy of the real archive without publishing content, results, or screenshots.
- Errors and logs must not include message text or private file content by default.

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

- After the archive arrives, inventory real formats, including how images and file attachments are represented; preserve the raw archive locally and implement adapters for observed formats.
- Acceptance: complete report, retryable import, unknowns preserved/reported, verifiable provenance, and attachments retained with links to their messages; validation against a copy of the real archive runs locally and is not included in Git.

### Phase 4 — PC/Android UI and Graph

- Search, context, provenance, graph exploration, LAN access, and incremental cache/sync.
- Add image/file gallery and supported previews, access to originals, and offline availability for synced attachments.
- Acceptance: demonstrated use on PC and Android; files open from their source message, and conflicts/incomplete transfers are visible.

### Phase 5 — Semantic Search and Local Models

- Integrate local models such as Qwen, gpt-oss-20b, and Gemma 4 through compatible runtimes.
- Configurable local embedding provider, model/version metadata, lexical/semantic fusion over text extracted from supported formats.
- Optional local OCR/visual description/embeddings can be added as derived processing without replacing original images.
- Acceptance: semantic results point to identifiable passages/attachments; re-embedding does not alter RAW.

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
- **Local model availability:** the core works with lexical search without embeddings; configure semantic search later for Qwen, gpt-oss-20b, Gemma 4, or other compatible models.

## 13. Decision History

- **2026-10-01:** The user confirmed Windows PC and Android as target devices, usually on the same home network, the repository under `D:\AI\PersonalMemory`, GitHub for versioning, a later ChatGPT archive, and future integration with local models Qwen, gpt-oss-20b, and Gemma 4, plus OpenCode and Hermes clients/agents.
- **2026-10-01:** The user confirmed building our own system if existing products do not meet the requirements, and requested documenting the comparison and added value as a portfolio project.
- **2026-10-01:** OpenAI documentation confirms MCP apps are web-only, connect to remote servers, and may require a Secure MCP Tunnel for private-network servers; direct mobile MCP access is not assumed.
- **2026-10-01:** The user specified that GitHub will contain synthetic data only for possible open-source publication; personal conversations will be used only locally in the created instance.
- The ChatGPT export was inspected locally; the importer follows the observed graph-shaped message structure.
