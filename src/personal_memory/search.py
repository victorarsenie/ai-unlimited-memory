"""Read-only lexical search over messages and their provenance."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


class SearchQueryError(ValueError):
    """Raised when an FTS query is empty, too long, or invalid."""


def search_messages(
    connection: sqlite3.Connection,
    query: str,
    *,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    normalized = query.strip()
    if not normalized:
        raise SearchQueryError("Query must contain at least one non-space character.")
    if len(normalized) > 256:
        raise SearchQueryError("Query must not exceed 256 characters.")
    if not 1 <= limit <= 100:
        raise SearchQueryError("Limit must be between 1 and 100.")
    if not 0 <= offset <= 10000:
        raise SearchQueryError("Offset must be between 0 and 10000.")

    try:
        total = connection.execute(
            "SELECT count(*) FROM messages_fts WHERE messages_fts MATCH ?",
            (normalized,),
        ).fetchone()[0]
        rows = connection.execute(
            """SELECT m.message_id, m.external_id, m.conversation_id,
                      c.source_id, c.title AS conversation_title,
                      m.sequence_number, m.role, m.author, m.created_at,
                      m.parent_message_id, m.branch_id, m.is_selected_variant,
                      m.source_locator_json,
                      snippet(messages_fts, 5, '', '', ' … ', 24) AS excerpt,
                      bm25(messages_fts) AS score,
                      (SELECT ro.relative_path
                         FROM source_files AS sf
                         JOIN raw_objects AS ro ON ro.sha256 = sf.raw_sha256
                        WHERE sf.source_id = c.source_id AND sf.file_role = 'archive'
                        ORDER BY sf.added_at
                        LIMIT 1) AS raw_archive_path
                 FROM messages_fts
                 JOIN messages AS m ON m.rowid = messages_fts.rowid
                 JOIN conversations AS c ON c.conversation_id = m.conversation_id
                WHERE messages_fts MATCH ?
                ORDER BY score, m.created_at, m.conversation_id, m.sequence_number
                LIMIT ? OFFSET ?""",
            (normalized, limit, offset),
        ).fetchall()
    except sqlite3.OperationalError as error:
        raise SearchQueryError("The search expression is not valid FTS5 syntax.") from error

    results = []
    for row in rows:
        results.append(
            {
                "messageId": row["message_id"],
                "externalId": row["external_id"],
                "conversationId": row["conversation_id"],
                "sourceId": row["source_id"],
                "conversationTitle": row["conversation_title"],
                "sequenceNumber": row["sequence_number"],
                "role": row["role"],
                "author": row["author"],
                "createdAt": row["created_at"],
                "parentMessageId": row["parent_message_id"],
                "branchId": row["branch_id"],
                "isSelectedVariant": bool(row["is_selected_variant"]),
                "excerpt": row["excerpt"],
                "score": row["score"],
                "provenance": {
                    "rawArchivePath": row["raw_archive_path"],
                    "sourceLocator": json.loads(row["source_locator_json"] or "{}"),
                },
            }
        )
    return {"query": normalized, "total": total, "limit": limit, "offset": offset, "results": results}
