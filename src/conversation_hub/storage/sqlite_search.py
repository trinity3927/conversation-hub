from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


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


def load_conversations_sqlite(input_path: str | Path) -> list[Conversation]:
    connection = sqlite3.connect(Path(input_path))
    connection.row_factory = sqlite3.Row
    try:
        conversation_rows = connection.execute(
            """
            SELECT
                source,
                id,
                title,
                created_at,
                updated_at,
                tags_json,
                metadata_json
            FROM conversations
            ORDER BY
                coalesce(julianday(updated_at), julianday(created_at), 0) DESC,
                source ASC,
                id ASC
            """
        ).fetchall()

        return [_conversation_from_row(connection, row) for row in conversation_rows]
    finally:
        connection.close()


def _conversation_from_row(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
) -> Conversation:
    participant_lookup = _load_participants(connection, row["source"], row["id"])

    return Conversation(
        id=row["id"],
        source=row["source"],
        title=row["title"],
        participants=list(participant_lookup.values()),
        messages=_load_messages(connection, row["source"], row["id"], participant_lookup),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        tags=_load_json_list(row["tags_json"]),
        metadata=_load_json_object(row["metadata_json"]),
    )


def _load_participants(
    connection: sqlite3.Connection,
    source: str,
    conversation_id: str,
) -> dict[str, Participant]:
    rows = connection.execute(
        """
        SELECT
            participant_key,
            participant_id,
            role,
            display_name,
            metadata_json
        FROM participants
        WHERE conversation_source = ? AND conversation_id = ?
        ORDER BY sort_index ASC
        """,
        (source, conversation_id),
    ).fetchall()

    return {
        row["participant_key"]: Participant(
            id=row["participant_id"],
            role=row["role"],
            display_name=row["display_name"],
            metadata=_load_json_object(row["metadata_json"]),
        )
        for row in rows
    }


def _load_messages(
    connection: sqlite3.Connection,
    source: str,
    conversation_id: str,
    participant_lookup: dict[str, Participant],
) -> list[Message]:
    rows = connection.execute(
        """
        SELECT
            id,
            participant_key,
            created_at,
            metadata_json
        FROM messages
        WHERE conversation_source = ? AND conversation_id = ?
        ORDER BY sort_index ASC
        """,
        (source, conversation_id),
    ).fetchall()

    return [
        Message(
            id=row["id"],
            participant=participant_lookup.get(row["participant_key"]),
            parts=_load_parts(connection, source, conversation_id, row["id"]),
            created_at=row["created_at"],
            metadata=_load_json_object(row["metadata_json"]),
        )
        for row in rows
    ]


def _load_parts(
    connection: sqlite3.Connection,
    source: str,
    conversation_id: str,
    message_id: str,
) -> list[ContentPart]:
    rows = connection.execute(
        """
        SELECT kind, text, metadata_json
        FROM content_parts
        WHERE conversation_source = ? AND conversation_id = ? AND message_id = ?
        ORDER BY part_index ASC
        """,
        (source, conversation_id, message_id),
    ).fetchall()

    return [
        ContentPart(
            kind=row["kind"],
            text=row["text"],
            metadata=_load_json_object(row["metadata_json"]),
        )
        for row in rows
    ]


def _load_json_object(payload: str) -> dict[str, object]:
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("SQLite JSON payload must decode to an object")
    return dict(data)


def _load_json_list(payload: str) -> list[str]:
    data = json.loads(payload)
    if not isinstance(data, list):
        raise ValueError("SQLite JSON payload must decode to a list")
    return [str(item) for item in data]


SQLiteSearchMatch = SQLiteConversationSearchMatch
SQLiteSearchResults = SQLiteConversationSearchResult
