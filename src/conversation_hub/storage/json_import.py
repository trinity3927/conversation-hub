from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


def load_conversations_json(path: str | Path) -> list[Conversation]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Normalized conversation JSON must be a list of conversations")
    return conversations_from_list(payload)


def conversations_from_list(items: list[dict[str, Any]]) -> list[Conversation]:
    return [conversation_from_dict(item) for item in items]


def conversation_from_dict(payload: dict[str, Any]) -> Conversation:
    return Conversation(
        id=payload["id"],
        source=payload["source"],
        title=payload.get("title"),
        participants=[
            participant_from_dict(participant_payload)
            for participant_payload in payload.get("participants", [])
        ],
        messages=[message_from_dict(message_payload) for message_payload in payload.get("messages", [])],
        created_at=payload.get("created_at"),
        updated_at=payload.get("updated_at"),
        tags=list(payload.get("tags", [])),
        metadata=dict(payload.get("metadata", {})),
    )


def message_from_dict(payload: dict[str, Any]) -> Message:
    return Message(
        id=payload["id"],
        participant=participant_from_dict(payload.get("participant")),
        parts=[content_part_from_dict(part_payload) for part_payload in payload.get("parts", [])],
        created_at=payload.get("created_at"),
        metadata=dict(payload.get("metadata", {})),
    )


def participant_from_dict(payload: dict[str, Any] | None) -> Participant | None:
    if payload is None:
        return None

    return Participant(
        id=payload.get("id"),
        role=payload.get("role"),
        display_name=payload.get("display_name"),
        metadata=dict(payload.get("metadata", {})),
    )


def content_part_from_dict(payload: dict[str, Any]) -> ContentPart:
    return ContentPart(
        kind=payload.get("kind", "text"),
        text=payload.get("text"),
        metadata=dict(payload.get("metadata", {})),
    )
