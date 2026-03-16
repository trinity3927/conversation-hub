from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SQLiteConversationSearchMatch:
    source: str
    conversation_id: str
    title: str | None
    message_count: int
    excerpt: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "conversation_id": self.conversation_id,
            "title": self.title,
            "message_count": self.message_count,
            "excerpt": self.excerpt,
        }


@dataclass(frozen=True, slots=True)
class SQLiteConversationSearchResult:
    query: str
    limit: int
    result_count: int
    results: list[SQLiteConversationSearchMatch]

    def to_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "limit": self.limit,
            "result_count": self.result_count,
            "results": [result.to_dict() for result in self.results],
        }


def search_conversations_sqlite(
    input_path: str | Path,
    query: str,
    limit: int = 10,
) -> SQLiteConversationSearchResult:
    if limit < 1:
        raise ValueError("limit must be at least 1")

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")

    connection = sqlite3.connect(Path(input_path))
    try:
        rows = connection.execute(
            """
            SELECT
                conversations.source,
                conversations.id,
                conversations.title,
                (
                    SELECT COUNT(*)
                    FROM messages
                    WHERE messages.conversation_source = conversations.source
                        AND messages.conversation_id = conversations.id
                ) AS message_count,
                CASE
                    WHEN instr(lower(coalesce(conversations.title, '')), ?) > 0
                        THEN conversations.title
                    ELSE (
                        SELECT content_parts.text
                        FROM content_parts
                        JOIN messages
                            ON messages.conversation_source = content_parts.conversation_source
                            AND messages.conversation_id = content_parts.conversation_id
                            AND messages.id = content_parts.message_id
                        WHERE content_parts.conversation_source = conversations.source
                            AND content_parts.conversation_id = conversations.id
                            AND content_parts.text IS NOT NULL
                            AND instr(lower(content_parts.text), ?) > 0
                        ORDER BY messages.sort_index, content_parts.part_index
                        LIMIT 1
                    )
                END AS excerpt,
                CASE
                    WHEN instr(lower(coalesce(conversations.title, '')), ?) > 0
                        THEN 1
                    ELSE 0
                END AS title_match,
                coalesce(julianday(conversations.updated_at), julianday(conversations.created_at), 0)
                    AS sort_timestamp
            FROM conversations
            WHERE instr(lower(coalesce(conversations.title, '')), ?) > 0
                OR EXISTS (
                    SELECT 1
                    FROM content_parts
                    WHERE content_parts.conversation_source = conversations.source
                        AND content_parts.conversation_id = conversations.id
                        AND content_parts.text IS NOT NULL
                        AND instr(lower(content_parts.text), ?) > 0
                )
            ORDER BY title_match DESC, sort_timestamp DESC, conversations.source ASC, conversations.id ASC
            LIMIT ?
            """,
            (
                normalized_query.lower(),
                normalized_query.lower(),
                normalized_query.lower(),
                normalized_query.lower(),
                normalized_query.lower(),
                limit,
            ),
        ).fetchall()
    finally:
        connection.close()

    results = [
        SQLiteConversationSearchMatch(
            source=row[0],
            conversation_id=row[1],
            title=row[2],
            message_count=row[3],
            excerpt=row[4] or "",
        )
        for row in rows
    ]

    return SQLiteConversationSearchResult(
        query=normalized_query,
        limit=limit,
        result_count=len(results),
        results=results,
    )


SQLiteSearchMatch = SQLiteConversationSearchMatch
SQLiteSearchResults = SQLiteConversationSearchResult
