from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from conversation_hub.models.schema import Conversation, Participant


@dataclass(slots=True)
class SQLiteWriteResult:
    output_path: Path
    conversation_count: int
    participant_count: int
    message_count: int
    content_part_count: int


def write_conversations_sqlite(
    conversations: Iterable[Conversation],
    output_path: str | Path,
) -> SQLiteWriteResult:
    normalized_output_path = Path(output_path)
    normalized_output_path.parent.mkdir(parents=True, exist_ok=True)

    conversation_list = list(conversations)
    participant_count = 0
    message_count = 0
    content_part_count = 0

    connection = sqlite3.connect(normalized_output_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        _create_schema(connection)

        with connection:
            for conversation in conversation_list:
                _delete_managed_rows(connection, conversation.source, conversation.id)

                connection.execute(
                    """
                    INSERT INTO conversations (
                        source,
                        id,
                        title,
                        created_at,
                        updated_at,
                        tags_json,
                        metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conversation.source,
                        conversation.id,
                        conversation.title,
                        _timestamp_to_iso8601(conversation.created_at),
                        _timestamp_to_iso8601(conversation.updated_at),
                        _canonical_json(list(conversation.tags)),
                        _canonical_json(conversation.metadata),
                    ),
                )

                participant_keys = _insert_participants(connection, conversation)
                participant_count += len(participant_keys)

                messages = conversation.messages_in_chronological_order()
                for sort_index, message in enumerate(messages):
                    message_count += 1
                    connection.execute(
                        """
                        INSERT INTO messages (
                            conversation_source,
                            conversation_id,
                            id,
                            participant_key,
                            created_at,
                            metadata_json,
                            sort_index
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            conversation.source,
                            conversation.id,
                            message.id,
                            _participant_lookup_key(message.participant, participant_keys),
                            _timestamp_to_iso8601(message.created_at),
                            _canonical_json(message.metadata),
                            sort_index,
                        ),
                    )

                    for part_index, part in enumerate(message.parts):
                        content_part_count += 1
                        connection.execute(
                            """
                            INSERT INTO content_parts (
                                conversation_source,
                                conversation_id,
                                message_id,
                                part_index,
                                kind,
                                text,
                                metadata_json
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                conversation.source,
                                conversation.id,
                                message.id,
                                part_index,
                                part.kind,
                                part.text,
                                _canonical_json(part.metadata),
                            ),
                        )

    finally:
        connection.close()

    return SQLiteWriteResult(
        output_path=normalized_output_path,
        conversation_count=len(conversation_list),
        participant_count=participant_count,
        message_count=message_count,
        content_part_count=content_part_count,
    )


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            source TEXT NOT NULL,
            id TEXT NOT NULL,
            title TEXT,
            created_at TEXT,
            updated_at TEXT,
            tags_json TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            PRIMARY KEY (source, id)
        );

        CREATE TABLE IF NOT EXISTS participants (
            conversation_source TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            participant_key TEXT NOT NULL,
            participant_id TEXT,
            role TEXT,
            display_name TEXT,
            metadata_json TEXT NOT NULL,
            sort_index INTEGER NOT NULL,
            PRIMARY KEY (conversation_source, conversation_id, participant_key),
            FOREIGN KEY (conversation_source, conversation_id)
                REFERENCES conversations (source, id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            conversation_source TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            id TEXT NOT NULL,
            participant_key TEXT,
            created_at TEXT,
            metadata_json TEXT NOT NULL,
            sort_index INTEGER NOT NULL,
            PRIMARY KEY (conversation_source, conversation_id, id),
            FOREIGN KEY (conversation_source, conversation_id)
                REFERENCES conversations (source, id)
                ON DELETE CASCADE,
            FOREIGN KEY (conversation_source, conversation_id, participant_key)
                REFERENCES participants (conversation_source, conversation_id, participant_key)
                ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS content_parts (
            conversation_source TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            part_index INTEGER NOT NULL,
            kind TEXT NOT NULL,
            text TEXT,
            metadata_json TEXT NOT NULL,
            PRIMARY KEY (conversation_source, conversation_id, message_id, part_index),
            FOREIGN KEY (conversation_source, conversation_id, message_id)
                REFERENCES messages (conversation_source, conversation_id, id)
                ON DELETE CASCADE
        );
        """
    )


def _delete_managed_rows(connection: sqlite3.Connection, source: str, conversation_id: str) -> None:
    params = (source, conversation_id)
    connection.execute(
        "DELETE FROM content_parts WHERE conversation_source = ? AND conversation_id = ?",
        params,
    )
    connection.execute(
        "DELETE FROM messages WHERE conversation_source = ? AND conversation_id = ?",
        params,
    )
    connection.execute(
        "DELETE FROM participants WHERE conversation_source = ? AND conversation_id = ?",
        params,
    )
    connection.execute(
        "DELETE FROM conversations WHERE source = ? AND id = ?",
        params,
    )


def _insert_participants(
    connection: sqlite3.Connection,
    conversation: Conversation,
) -> dict[str, str]:
    messages = conversation.messages_in_chronological_order()
    fingerprint_to_key: dict[str, str] = {}

    for participant in conversation.participants:
        _ensure_participant_key(fingerprint_to_key, participant)

    for message in messages:
        if message.participant is not None:
            _ensure_participant_key(fingerprint_to_key, message.participant)

    for sort_index, (fingerprint, participant_key) in enumerate(fingerprint_to_key.items()):
        participant = _participant_from_fingerprint(fingerprint)
        connection.execute(
            """
            INSERT INTO participants (
                conversation_source,
                conversation_id,
                participant_key,
                participant_id,
                role,
                display_name,
                metadata_json,
                sort_index
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation.source,
                conversation.id,
                participant_key,
                participant.id,
                participant.role,
                participant.display_name,
                _canonical_json(participant.metadata),
                sort_index,
            ),
        )

    return fingerprint_to_key


def _participant_lookup_key(
    participant: Participant | None,
    fingerprint_to_key: dict[str, str],
) -> str | None:
    if participant is None:
        return None
    return fingerprint_to_key[_participant_fingerprint(participant)]


def _ensure_participant_key(
    fingerprint_to_key: dict[str, str],
    participant: Participant,
) -> None:
    fingerprint = _participant_fingerprint(participant)
    if fingerprint in fingerprint_to_key:
        return
    fingerprint_to_key[fingerprint] = f"participant-{len(fingerprint_to_key)}"


def _participant_fingerprint(participant: Participant) -> str:
    return _canonical_json(
        {
            "id": participant.id,
            "role": participant.role,
            "display_name": participant.display_name,
            "metadata": dict(participant.metadata),
        }
    )


def _participant_from_fingerprint(fingerprint: str) -> Participant:
    payload = json.loads(fingerprint)
    return Participant(
        id=payload.get("id"),
        role=payload.get("role"),
        display_name=payload.get("display_name"),
        metadata=dict(payload.get("metadata", {})),
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _timestamp_to_iso8601(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
