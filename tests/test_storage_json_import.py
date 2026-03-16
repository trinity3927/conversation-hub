from __future__ import annotations

import json

import conversation_hub.storage as storage
from conversation_hub.models.schema import Conversation


def test_load_conversations_json_round_trips_normalized_payload(tmp_path) -> None:
    payload = [
        {
            "id": "conv-1",
            "source": "chatgpt",
            "title": "Taildrop release checklist",
            "participants": [
                {
                    "id": "user",
                    "role": "user",
                    "display_name": "Alex",
                    "metadata": {"team": "ops"},
                },
                {
                    "id": "assistant",
                    "role": "assistant",
                    "display_name": None,
                    "metadata": {},
                },
            ],
            "messages": [
                {
                    "id": "msg-1",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": "Alex",
                        "metadata": {"team": "ops"},
                    },
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Draft a Taildrop release checklist.",
                            "metadata": {},
                        }
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
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Here is the checklist.",
                            "metadata": {},
                        },
                        {
                            "kind": "image",
                            "text": None,
                            "metadata": {"asset_id": "asset-1"},
                        },
                    ],
                    "created_at": "2024-03-09T16:00:05+00:00",
                    "metadata": {"source_id": "raw-2"},
                },
            ],
            "created_at": "2024-03-09T16:00:00+00:00",
            "updated_at": "2024-03-09T16:05:00+00:00",
            "tags": ["ops"],
            "metadata": {"workspace": "conversation-hub"},
        }
    ]
    input_path = tmp_path / "normalized.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    conversations = storage.load_conversations_json(input_path)

    assert len(conversations) == 1
    conversation = conversations[0]
    assert isinstance(conversation, Conversation)
    assert conversation.id == "conv-1"
    assert conversation.created_at.isoformat() == "2024-03-09T16:00:00+00:00"
    assert conversation.participants[0].display_name == "Alex"
    assert conversation.messages[0].participant.role == "user"
    assert conversation.messages[1].parts[1].kind == "image"
    assert conversation.messages[1].metadata == {"source_id": "raw-2"}
    assert storage.conversations_to_list(conversations) == payload
