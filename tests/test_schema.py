from __future__ import annotations

from datetime import datetime, timezone

from conversation_hub.models.schema import (
    ContentPart,
    Conversation,
    Message,
    Participant,
    normalize_timestamp,
)


def test_message_exposes_joined_text_content_from_parts() -> None:
    message = Message(
        id="msg-1",
        participant=Participant(id="assistant", role="assistant"),
        parts=[
            ContentPart(text="Hello"),
            ContentPart(kind="image", metadata={"url": "https://example.com/image.png"}),
            ContentPart(text=", world"),
        ],
    )

    assert message.text_content == "Hello, world"


def test_conversation_can_return_messages_in_chronological_order() -> None:
    conversation = Conversation(
        id="conv-1",
        source="test",
        messages=[
            Message(
                id="msg-late",
                participant=Participant(id="assistant", role="assistant"),
                parts=[ContentPart(text="second")],
                created_at="2024-03-09T16:00:05Z",
            ),
            Message(
                id="msg-early",
                participant=Participant(id="user", role="user"),
                parts=[ContentPart(text="first")],
                created_at="2024-03-09T16:00:01Z",
            ),
            Message(
                id="msg-unknown",
                participant=Participant(id="assistant", role="assistant"),
                parts=[ContentPart(text="no timestamp")],
            ),
        ],
    )

    assert [message.id for message in conversation.messages_in_chronological_order()] == [
        "msg-early",
        "msg-late",
        "msg-unknown",
    ]
    assert [message.id for message in conversation.messages] == [
        "msg-late",
        "msg-early",
        "msg-unknown",
    ]


def test_normalize_timestamp_accepts_epoch_seconds_and_iso_strings() -> None:
    expected = datetime(2024, 3, 9, 16, 0, 0, tzinfo=timezone.utc)

    assert normalize_timestamp(1710000000) == expected
    assert normalize_timestamp("2024-03-09T16:00:00Z") == expected
