-- Keep a rebuildable full-text index in sync with canonical message records.

CREATE VIRTUAL TABLE messages_fts USING fts5(
    message_id UNINDEXED,
    conversation_id UNINDEXED,
    source_id UNINDEXED,
    title,
    role,
    content_text,
    tokenize = 'unicode61 remove_diacritics 2'
);

INSERT INTO messages_fts(rowid, message_id, conversation_id, source_id, title, role, content_text)
SELECT m.rowid, m.message_id, m.conversation_id, c.source_id,
       COALESCE(c.title, ''), COALESCE(m.role, ''), m.content_text
FROM messages AS m
JOIN conversations AS c ON c.conversation_id = m.conversation_id;

CREATE TRIGGER messages_fts_after_insert
AFTER INSERT ON messages
BEGIN
    INSERT INTO messages_fts(rowid, message_id, conversation_id, source_id, title, role, content_text)
    SELECT new.rowid, new.message_id, new.conversation_id, c.source_id,
           COALESCE(c.title, ''), COALESCE(new.role, ''), new.content_text
    FROM conversations AS c
    WHERE c.conversation_id = new.conversation_id;
END;

CREATE TRIGGER messages_fts_after_delete
AFTER DELETE ON messages
BEGIN
    DELETE FROM messages_fts WHERE rowid = old.rowid;
END;

CREATE TRIGGER messages_fts_after_update
AFTER UPDATE OF message_id, conversation_id, role, content_text ON messages
BEGIN
    DELETE FROM messages_fts WHERE rowid = old.rowid;
    INSERT INTO messages_fts(rowid, message_id, conversation_id, source_id, title, role, content_text)
    SELECT new.rowid, new.message_id, new.conversation_id, c.source_id,
           COALESCE(c.title, ''), COALESCE(new.role, ''), new.content_text
    FROM conversations AS c
    WHERE c.conversation_id = new.conversation_id;
END;

CREATE TRIGGER conversations_fts_after_update
AFTER UPDATE OF title, source_id ON conversations
BEGIN
    DELETE FROM messages_fts WHERE conversation_id = old.conversation_id;
    INSERT INTO messages_fts(rowid, message_id, conversation_id, source_id, title, role, content_text)
    SELECT m.rowid, m.message_id, m.conversation_id, new.source_id,
           COALESCE(new.title, ''), COALESCE(m.role, ''), m.content_text
    FROM messages AS m
    WHERE m.conversation_id = new.conversation_id;
END;
