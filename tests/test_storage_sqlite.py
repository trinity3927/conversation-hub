from __future__ import annotations

import sqlite3

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant
from conversation_hub.storage.sqlite_store import SQLiteWriteResult, write_conversations_sqlite


def test_write_conversations_sqlite_creates_expected_tables_and_rows(tmp_path) -> None:
    output_path = tmp_path / "conversations.db"

    result = write_conversations_sqlite(_sample_conversations(), output_path)

    assert output_path.exists()
    assert result == SQLiteWriteResult(
        output_path=output_path,
        conversation_count=1,
        participant_count=2,
        message_count=2,
        content_part_count=3,
    )

    connection = sqlite3.connect(output_path)
    try:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
            )
        }
        assert table_names >= {
            "content_parts",
            "conversations",
            "messages",
            "participants",
        }

        assert connection.execute(
            """
            SELECT
                id,
                source,
                title,
                created_at,
                updated_at,
                tags_json,
                metadata_json
            FROM conversations
            """
        ).fetchall() == [
            (
                "conv-1",
                "chatgpt",
                "Taildrop release checklist",
                "2024-03-09T16:00:00+00:00",
                "2024-03-09T16:05:00+00:00",
                '["ops","release"]',
                '{"priority":1,"workspace":"conversation-hub"}',
            )
        ]

        assert connection.execute(
            """
            SELECT
                conversation_id,
                participant_key,
                participant_id,
                role,
                display_name,
                metadata_json,
                sort_index
            FROM participants
            ORDER BY sort_index
            """
        ).fetchall() == [
            (
                "conv-1",
                "participant-0",
                "user",
                "user",
                "Alex",
                '{"team":"ops"}',
                0,
            ),
            (
                "conv-1",
                "participant-1",
                "assistant",
                "assistant",
                None,
                "{}",
                1,
            ),
        ]

        assert connection.execute(
            """
            SELECT
                conversation_id,
                id,
                participant_key,
                created_at,
                metadata_json,
                sort_index
            FROM messages
            ORDER BY sort_index
            """
        ).fetchall() == [
            (
                "conv-1",
                "msg-1",
                "participant-0",
                "2024-03-09T16:00:01+00:00",
                "{}",
                0,
            ),
            (
                "conv-1",
                "msg-2",
                "participant-1",
                "2024-03-09T16:00:05+00:00",
                '{"source_id":"raw-2"}',
                1,
            ),
        ]

        assert connection.execute(
            """
            SELECT
                conversation_id,
                message_id,
                part_index,
                kind,
                text,
                metadata_json
            FROM content_parts
            ORDER BY message_id, part_index
            """
        ).fetchall() == [
            (
                "conv-1",
                "msg-1",
                0,
                "text",
                "Draft a Taildrop release checklist.",
                "{}",
            ),
            (
                "conv-1",
                "msg-2",
                0,
                "text",
                "Here is the checklist.",
                "{}",
            ),
            (
                "conv-1",
                "msg-2",
                1,
                "image",
                None,
                '{"asset_id":"asset-1"}',
            ),
        ]
    finally:
        connection.close()


def test_write_conversations_sqlite_rewrites_managed_rows_without_duplicates(tmp_path) -> None:
    output_path = tmp_path / "conversations.db"
    conversations = _sample_conversations()

    write_conversations_sqlite(conversations, output_path)
    result = write_conversations_sqlite(conversations, output_path)

    assert result.conversation_count == 1
    assert result.message_count == 2

    connection = sqlite3.connect(output_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM conversations").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM participants").fetchone() == (2,)
        assert connection.execute("SELECT COUNT(*) FROM messages").fetchone() == (2,)
        assert connection.execute("SELECT COUNT(*) FROM content_parts").fetchone() == (3,)
    finally:
        connection.close()


def _sample_conversations() -> list[Conversation]:
    return [
        Conversation(
            id="conv-1",
            source="chatgpt",
            title="Taildrop release checklist",
            participants=[
                Participant(
                    id="user",
                    role="user",
                    display_name="Alex",
                    metadata={"team": "ops"},
                ),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[
                        ContentPart(text="Here is the checklist."),
                        ContentPart(kind="image", metadata={"asset_id": "asset-1"}),
                    ],
                    created_at="2024-03-09T16:00:05Z",
                    metadata={"source_id": "raw-2"},
                ),
                Message(
                    id="msg-1",
                    participant=Participant(
                        id="user",
                        role="user",
                        display_name="Alex",
                        metadata={"team": "ops"},
                    ),
                    parts=[ContentPart(text="Draft a Taildrop release checklist.")],
                    created_at="2024-03-09T16:00:01Z",
                ),
            ],
            created_at="2024-03-09T16:00:00Z",
            updated_at="2024-03-09T16:05:00Z",
            tags=["ops", "release"],
            metadata={"workspace": "conversation-hub", "priority": 1},
        )
    ]
