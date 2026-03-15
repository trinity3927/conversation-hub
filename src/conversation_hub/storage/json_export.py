from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


def conversations_to_list(conversations: Iterable[Conversation]) -> list[dict[str, Any]]:
    return [conversation_to_dict(conversation) for conversation in conversations]


def conversation_to_dict(conversation: Conversation) -> dict[str, Any]:
    return {
        "id": conversation.id,
        "source": conversation.source,
        "title": conversation.title,
        "participants": [participant_to_dict(participant) for participant in conversation.participants],
        "messages": [message_to_dict(message) for message in conversation.messages_in_chronological_order()],
        "created_at": _timestamp_to_iso8601(conversation.created_at),
        "updated_at": _timestamp_to_iso8601(conversation.updated_at),
        "tags": list(conversation.tags),
        "metadata": dict(conversation.metadata),
    }


def message_to_dict(message: Message) -> dict[str, Any]:
    return {
        "id": message.id,
        "participant": participant_to_dict(message.participant),
        "parts": [content_part_to_dict(part) for part in message.parts],
        "created_at": _timestamp_to_iso8601(message.created_at),
        "metadata": dict(message.metadata),
    }


def participant_to_dict(participant: Participant | None) -> dict[str, Any] | None:
    if participant is None:
        return None

    return {
        "id": participant.id,
        "role": participant.role,
        "display_name": participant.display_name,
        "metadata": dict(participant.metadata),
    }


def content_part_to_dict(part: ContentPart) -> dict[str, Any]:
    return {
        "kind": part.kind,
        "text": part.text,
        "metadata": dict(part.metadata),
    }


def _timestamp_to_iso8601(value: datetime | None) -> str | None:
    if value is None:
        return None

    return value.isoformat()
