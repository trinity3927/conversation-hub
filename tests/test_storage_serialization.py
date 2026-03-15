from __future__ import annotations

import conversation_hub.storage as storage
from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


def test_conversation_to_dict_serializes_nested_models_with_iso_timestamps() -> None:
    conversation = Conversation(
        id="conv-1",
        source="chatgpt",
        title="Launch notes",
        participants=[
            Participant(
                id="user",
                role="user",
                display_name="Alex",
                metadata={"team": "docs"},
            )
        ],
        messages=[
            Message(
                id="msg-2",
                participant=Participant(id="assistant", role="assistant"),
                parts=[ContentPart(text="Second message")],
                created_at="2024-03-09T16:00:05Z",
                metadata={"source_id": "raw-2"},
            ),
            Message(
                id="msg-1",
                participant=Participant(
                    id="user",
                    role="user",
                    display_name="Alex",
                    metadata={"team": "docs"},
                ),
                parts=[
                    ContentPart(text="First message"),
                    ContentPart(kind="image", metadata={"asset_id": "asset-1"}),
                ],
                created_at="2024-03-09T16:00:01Z",
            ),
        ],
        created_at="2024-03-09T16:00:00Z",
        updated_at="2024-03-09T16:05:00Z",
        tags=["hackathon"],
        metadata={"workspace": "conversation-hub"},
    )

    assert storage.conversation_to_dict(conversation) == {
        "id": "conv-1",
        "source": "chatgpt",
        "title": "Launch notes",
        "participants": [
            {
                "id": "user",
                "role": "user",
                "display_name": "Alex",
                "metadata": {"team": "docs"},
            }
        ],
        "messages": [
            {
                "id": "msg-1",
                "participant": {
                    "id": "user",
                    "role": "user",
                    "display_name": "Alex",
                    "metadata": {"team": "docs"},
                },
                "parts": [
                    {"kind": "text", "text": "First message", "metadata": {}},
                    {"kind": "image", "text": None, "metadata": {"asset_id": "asset-1"}},
                ],
                "created_at": "2024-03-09T16:00:01+00:00",
                "metadata": {},
            },
            {
                "id": "msg-2",
                "participant": {
                    "id": "assistant",
                    "role": "assistant",
                    "display_name": None,
                    "metadata": {},
                },
                "parts": [{"kind": "text", "text": "Second message", "metadata": {}}],
                "created_at": "2024-03-09T16:00:05+00:00",
                "metadata": {"source_id": "raw-2"},
            },
        ],
        "created_at": "2024-03-09T16:00:00+00:00",
        "updated_at": "2024-03-09T16:05:00+00:00",
        "tags": ["hackathon"],
        "metadata": {"workspace": "conversation-hub"},
    }
