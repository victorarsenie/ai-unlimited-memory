-- Preserve imported conversation records and their source structure. The original export in RAW remains authoritative for byte-for-byte fidelity.

ALTER TABLE conversations ADD COLUMN source_locator_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE messages ADD COLUMN parent_message_id TEXT REFERENCES messages(message_id);
ALTER TABLE messages ADD COLUMN branch_id TEXT;
ALTER TABLE messages ADD COLUMN variant_group_id TEXT;
ALTER TABLE messages ADD COLUMN is_selected_variant INTEGER NOT NULL DEFAULT 1 CHECK (is_selected_variant IN (0, 1));
ALTER TABLE messages ADD COLUMN source_locator_json TEXT NOT NULL DEFAULT '{}';
ALTER TABLE messages ADD COLUMN source_payload_json TEXT NOT NULL DEFAULT '{}';

CREATE TABLE message_parts (
    message_part_id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    part_index INTEGER NOT NULL CHECK (part_index >= 0),
    part_kind TEXT NOT NULL CHECK (part_kind IN ('text', 'image', 'file', 'audio', 'video', 'structured', 'unknown')),
    text_content TEXT,
    attachment_id TEXT REFERENCES attachments(attachment_id),
    payload_json TEXT NOT NULL DEFAULT '{}',
    source_locator_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (message_id, part_index)
);

CREATE TABLE conversation_captures (
    capture_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    import_run_id TEXT REFERENCES import_runs(import_run_id),
    capture_method TEXT NOT NULL,
    completeness TEXT NOT NULL DEFAULT 'unknown' CHECK (completeness IN ('complete', 'partial', 'unknown')),
    captured_at TEXT NOT NULL,
    source_file_id TEXT REFERENCES source_files(source_file_id),
    source_locator_json TEXT NOT NULL DEFAULT '{}',
    report_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX idx_messages_parent ON messages(parent_message_id);
CREATE INDEX idx_messages_branch ON messages(conversation_id, branch_id);
CREATE INDEX idx_message_parts_message ON message_parts(message_id, part_index);
CREATE INDEX idx_conversation_captures_conversation ON conversation_captures(conversation_id, captured_at);
