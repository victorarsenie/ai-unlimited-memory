# Personal Memory Implementation Plan

**Date:** 2026-10-01  
**Basis:** [System design](../superpowers/specs/2026-10-01-personal-memory-system-design.md)  
**Status:** The user approved evaluating existing solutions and building our own where needed on 2026-10-01; implementation proceeds incrementally.

The detailed requirements, scope, and portfolio rationale are in the [requirements document](../project/requirements-and-scope.md).

## Working Decisions

- The local PC repository is the source of truth; raw imports remain unchanged in RAW.
- INDEX contains normalized data and rebuildable indexes; DERIVED contains linked relations, summaries, and vectors with source provenance.
- Before writing code, compare existing products against requirements and try configuring the best fit. Build custom components only for confirmed gaps. If a custom core remains necessary, the initial option is SQLite/FTS5 and a Python/FastAPI API; choose the runtime after inspecting the available environment.
- The ChatGPT importer is modular: define the adapter contract first, then implement a concrete parser only after receiving and inspecting the real archive.
- For Android, begin with an installable web interface accessible on the LAN. Decide on bidirectional offline sync and native app after validating the prototype and actual usage requirements.
- Add MCP, Qwen, OpenCode, and Hermes as adapters over the stable API and data model, not as core dependencies.
- Every phase preserves provenance (source, locator, import time, transformation, and related identifiers) and allows reindexing without changing RAW.

## Phases and Acceptance Criteria

### 0. Evaluate Existing Solutions (before implementation)

The initial comparison is documented in [Existing-solutions comparison](../research/existing-solutions-comparison.md). The user confirmed that custom development is appropriate if existing products do not meet the requirements, and that the rationale/comparison should be included in portfolio documentation.

- Practically evaluate Khoj, Open WebUI, AnythingLLM, and Memos against priority requirements: local data, local models, Android/browser on LAN, archive import, RAW preservation, provenance, relationship map, and MCP.
- For one or two candidates, review current documentation and create a prototype with synthetic data; do not import the real ChatGPT archive before inspecting it.
- Acceptance: clear comparison and recommendation: (a) configure an existing product, (b) use it as UI over a custom repository/API, or (c) implement the core, explaining the gaps that justify the effort.
- Verification: manual walkthrough on PC and Android where possible; record unmet requirements and any ChatGPT/MCP access limitations.
- The user approved a custom core with reuse of existing products where helpful; refine the specific product choices and adapters after practical evaluation.

### 1. Foundation and Data Contracts

- Inspect the environment and existing documentation; record actual runtime choices and directory structure.
- Define `RAW/`, `INDEX/`, `DERIVED/`, local configuration, and backup rules.
- Define the initial schema for sources, conversations, messages, attachments, entities, relationships, and provenance; use versioned migrations.
- Acceptance: an empty repository can be initialized reproducibly; transformations and reindexing never overwrite source data.
- Verification: manually review the schema, directories, and initialization instructions.

### 2. Local API and Lexical Search

- Add versioned local endpoints for service health, sources, search, and reading provenance-linked items.
- Configure SQLite FTS5 for lexical search, filtering, and navigation back to source.
- Add a documented generic import for text content and metadata without claiming compatibility with an uninspected ChatGPT export.
- Acceptance: the user can add, search, and open indexed content; each result identifies its source and location.
- Verification: manual walkthrough using clearly labeled synthetic data, not real personal data.

### 3. Modular ChatGPT Importer

- Define the adapter interface, import report, and policies for duplicates, attachments, and errors.
- When the archive is available, inspect its structure and included documentation before implementing the concrete parser.
- Preserve original files exactly; write extracted content and indexes only to their designated areas.
- Acceptance: import is retryable/idempotent, reports accepted/rejected content, and allows indexes to be rebuilt from RAW.
- Verification: manually validate against copies of the real archive, checking item counts and provenance.

### 4. Exploration Interface and Android LAN Access

- Build UI for search, conversation/source navigation, and provenance inspection.
- Add graph visualization as an exploration layer over approved/derived entities and relationships.
- Configure controlled local access, clear PC/phone instructions, and useful behavior when the server is unavailable.
- Acceptance: PC and phone on the same network can access the system; UI shows sources and links without exposing raw directories.
- Verification: manual walkthrough on PC and Android over the local network.

### 5. Semantic Search and Local Integration

- Add a replaceable embeddings interface with a local Qwen provider or another runtime configured later.
- Store vectors only in INDEX/DERIVED and link each vector to the model version and source text.
- Add semantic search and fusion with FTS without requiring a cloud model.
- Acceptance: changing the model allows re-embedding without touching RAW; results preserve provenance.
- Verification: manual walkthrough with an available local model; if unavailable, clearly document the deferred functionality.

### 6. MCP Bridge and Agent Adapters

- Publish an MCP bridge with a restricted initial read-only set: search, read, map, and provenance.
- Keep adapters for ChatGPT, OpenCode, and Hermes separate from the central server and schema.
- Add write operations only after authorization, validation, and change logging are defined.
- Acceptance: supported clients can find and read the same data through API/MCP, with each result's source visible.
- Verification: manually connect each client after checking its support and configuration.

### 7. Synchronization, Security, and Backup

- Evaluate a PC-authoritative model with local Android replica/cache and queues for offline changes.
- Document LAN authentication, minimal port exposure, backup, and restoration.
- Consider remote access only on request through a private tunnel; no router port forwarding by default.
- Acceptance: backup/restore and conflict handling are explained before bidirectional sync is enabled.
- Verification: manual backup and recovery walkthrough on local copies.

## Dependency Order

Foundation → API and FTS → concrete importer (after archive) and UI/LAN → semantic search and MCP → sync/hardening. UI prototyping can start once the API and minimal model are stable. Qwen/OpenCode/Hermes remain later adapters.

## Out of Scope for the First Slice

- Arbitrary interpretation of the ChatGPT archive before seeing it.
- Exposing the server directly to the internet.
- Autonomous agent writes of “memories” without approval and provenance.
- Choosing an Android replication format before measuring performance and the real PWA experience.
