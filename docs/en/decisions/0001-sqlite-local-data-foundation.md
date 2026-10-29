# ADR-0001: SQLite as the Initial Local Canonical Database

## Status

Accepted for the first implementation increment.

## Date

2026-10-01

## Context

Windows and Android are intended to keep complete local replicas with bidirectional synchronization. The first implementation must work locally on Windows, preserve imported files byte-for-byte, keep personal data outside Git, and model sources, conversations, messages, attachments, knowledge-graph records, and provenance. The received archive was inspected locally; the concrete parser must follow the observed structure and retain unknown payloads linked to RAW.

The inspected environment has Python 3.12 and SQLite with FTS5 available. FastAPI and Uvicorn are not installed. The first increment should not require downloading dependencies or starting a network service.

## Decision

Use SQLite for the initial canonical metadata database and Python's standard library for initialization and versioned SQL migrations. Store the database under `INDEX/`; create `RAW/`, `INDEX/`, `DERIVED/`, and `backups/` in a per-user data directory outside the Git checkout. The default Windows location is `%LOCALAPPDATA%\PersonalMemory`; allow `PERSONAL_MEMORY_HOME` or `--data-dir` to select another location.

Store original bytes as content-addressed objects under RAW, identified by SHA-256. The database stores metadata and relationships to those objects. Keep extracted text, OCR, thumbnails, embeddings, and other rebuildable artifacts in DERIVED or regenerable indexes. Migration files are immutable after application and are checked by SHA-256.

## Alternatives Considered

### PostgreSQL

- Provides multi-user concurrency and a server model.
- Adds installation and operational work that is not needed for a single-PC first increment.
- Reconsider if measured concurrency or remote access requires a separate database server.

### A document database or a single JSON file

- Flexible for unknown input formats.
- Weakens relational integrity for provenance, attachments, and knowledge-graph links; migration and query behavior would be harder to audit.
- Rejected for the canonical layer; unknown source payloads remain intact in RAW and may be represented in metadata JSON.

### Add FastAPI and an ORM immediately

- Could accelerate a REST API and application models.
- Neither dependency is present in the inspected runtime, and the API contract is not yet implemented.
- Deferred until the API increment selects and documents its runtime/dependencies.

## Consequences

- The first increment is local, dependency-free, and straightforward to back up.
- SQLite supports relational provenance and FTS5 is available for a later lexical-search increment.
- The database remains a single-writer store; the Android replica and synchronization protocol need separate design.
- SQL migrations and application-level validation must evolve without rewriting applied migrations.
- This decision does not choose the API framework, embedding provider, or Android client technology.
