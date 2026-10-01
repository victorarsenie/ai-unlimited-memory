-- Canonical metadata schema. Original file bytes remain in RAW; this database
-- records stable identities, relationships, and provenance to those originals.

CREATE TABLE sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    origin_uri TEXT,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE import_runs (
    import_run_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    adapter_name TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'partial', 'failed')),
    report_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE raw_objects (
    sha256 TEXT PRIMARY KEY CHECK (length(sha256) = 64),
    relative_path TEXT NOT NULL UNIQUE,
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
    observed_mime_type TEXT,
    first_seen_at TEXT NOT NULL
);

CREATE TABLE source_files (
    source_file_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    raw_sha256 TEXT NOT NULL REFERENCES raw_objects(sha256),
    file_role TEXT NOT NULL CHECK (file_role IN ('archive', 'document', 'attachment', 'other')),
    original_filename TEXT,
    added_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    external_id TEXT,
    title TEXT,
    created_at TEXT,
    updated_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (source_id, external_id)
);

CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
    external_id TEXT,
    sequence_number INTEGER NOT NULL CHECK (sequence_number >= 0),
    role TEXT,
    author TEXT,
    created_at TEXT,
    content_text TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (conversation_id, sequence_number),
    UNIQUE (conversation_id, external_id)
);

CREATE TABLE attachments (
    attachment_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    message_id TEXT REFERENCES messages(message_id) ON DELETE SET NULL,
    raw_sha256 TEXT NOT NULL REFERENCES raw_objects(sha256),
    original_filename TEXT,
    observed_mime_type TEXT,
    attached_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    raw_sha256 TEXT REFERENCES raw_objects(sha256),
    title TEXT NOT NULL,
    observed_mime_type TEXT,
    created_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE entities (
    entity_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    review_state TEXT NOT NULL DEFAULT 'derived'
        CHECK (review_state IN ('derived', 'confirmed', 'contested', 'rejected')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE claims (
    claim_id TEXT PRIMARY KEY,
    claim_text TEXT NOT NULL,
    review_state TEXT NOT NULL DEFAULT 'derived'
        CHECK (review_state IN ('derived', 'confirmed', 'contested', 'rejected')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE relations (
    relation_id TEXT PRIMARY KEY,
    subject_entity_id TEXT NOT NULL REFERENCES entities(entity_id),
    predicate TEXT NOT NULL,
    object_entity_id TEXT REFERENCES entities(entity_id),
    object_value TEXT,
    review_state TEXT NOT NULL DEFAULT 'derived'
        CHECK (review_state IN ('derived', 'confirmed', 'contested', 'rejected')),
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    CHECK ((object_entity_id IS NOT NULL) <> (object_value IS NOT NULL))
);

CREATE TABLE provenance (
    provenance_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    conversation_id TEXT REFERENCES conversations(conversation_id),
    message_id TEXT REFERENCES messages(message_id),
    document_id TEXT REFERENCES documents(document_id),
    attachment_id TEXT REFERENCES attachments(attachment_id),
    locator_json TEXT NOT NULL DEFAULT '{}',
    evidence_text TEXT,
    derivation_method TEXT NOT NULL,
    processor_name TEXT,
    processor_version TEXT,
    created_at TEXT NOT NULL,
    CHECK (
        conversation_id IS NOT NULL OR message_id IS NOT NULL OR
        document_id IS NOT NULL OR attachment_id IS NOT NULL
    )
);

CREATE TABLE entity_provenance (
    entity_id TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE CASCADE,
    provenance_id TEXT NOT NULL REFERENCES provenance(provenance_id) ON DELETE CASCADE,
    PRIMARY KEY (entity_id, provenance_id)
);

CREATE TABLE claim_provenance (
    claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    provenance_id TEXT NOT NULL REFERENCES provenance(provenance_id) ON DELETE CASCADE,
    PRIMARY KEY (claim_id, provenance_id)
);

CREATE TABLE relation_provenance (
    relation_id TEXT NOT NULL REFERENCES relations(relation_id) ON DELETE CASCADE,
    provenance_id TEXT NOT NULL REFERENCES provenance(provenance_id) ON DELETE CASCADE,
    PRIMARY KEY (relation_id, provenance_id)
);

CREATE INDEX idx_import_runs_source ON import_runs(source_id, started_at);
CREATE INDEX idx_source_files_source ON source_files(source_id);
CREATE INDEX idx_conversations_source ON conversations(source_id, created_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id, sequence_number);
CREATE INDEX idx_attachments_message ON attachments(message_id);
CREATE INDEX idx_documents_source ON documents(source_id);
CREATE INDEX idx_entities_name ON entities(canonical_name);
CREATE INDEX idx_relations_subject ON relations(subject_entity_id, predicate);
CREATE INDEX idx_provenance_source ON provenance(source_id);
CREATE INDEX idx_provenance_message ON provenance(message_id);
CREATE INDEX idx_provenance_document ON provenance(document_id);
