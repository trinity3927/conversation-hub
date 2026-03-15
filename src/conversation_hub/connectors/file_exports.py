from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from conversation_hub.connectors.base import Connector
from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


class ChatGPTExportConnector(Connector):
    source_name = "chatgpt"

    def __init__(self, export_path: str | Path) -> None:
        self.export_path = Path(export_path)

    def fetch(self) -> Iterable[Conversation]:
        for raw_conversation in _load_conversation_records(self.export_path):
            messages = _parse_chatgpt_messages(raw_conversation.get("mapping"))
            yield Conversation(
                id=str(raw_conversation["id"]),
                source=self.source_name,
                title=raw_conversation.get("title"),
                created_at=raw_conversation.get("create_time"),
                updated_at=raw_conversation.get("update_time"),
                messages=messages,
                participants=_participants_from_messages(messages),
            )


class ClaudeExportConnector(Connector):
    source_name = "claude"

    def __init__(self, export_path: str | Path) -> None:
        self.export_path = Path(export_path)

    def fetch(self) -> Iterable[Conversation]:
        for raw_conversation in _load_conversation_records(self.export_path):
            raw_messages = raw_conversation.get("messages") or raw_conversation.get("chat_messages") or []
            messages = [
                _parse_embedded_message(raw_message)
                for raw_message in raw_messages
                if isinstance(raw_message, dict)
            ]
            yield Conversation(
                id=str(raw_conversation.get("uuid") or raw_conversation["id"]),
                source=self.source_name,
                title=raw_conversation.get("name") or raw_conversation.get("title"),
                created_at=raw_conversation.get("created_at"),
                updated_at=raw_conversation.get("updated_at"),
                messages=messages,
                participants=_participants_from_messages(messages),
            )


def _load_conversation_records(export_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(export_path.read_text())
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        records = payload.get("conversations")
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
    raise ValueError(f"Unsupported export payload in {export_path}")


def _parse_chatgpt_messages(mapping: Any) -> list[Message]:
    if not isinstance(mapping, dict):
        return []

    messages: list[Message] = []
    for node in mapping.values():
        if not isinstance(node, dict):
            continue
        raw_message = node.get("message")
        if not isinstance(raw_message, dict):
            continue
        messages.append(
            Message(
                id=str(raw_message.get("id") or node["id"]),
                participant=_participant_from_role(
                    _as_dict(raw_message.get("author")).get("role")
                ),
                parts=_content_parts_from_payload(raw_message.get("content")),
                created_at=raw_message.get("create_time"),
                metadata=_as_dict(raw_message.get("metadata")),
            )
        )
    return messages


def _parse_embedded_message(raw_message: dict[str, Any]) -> Message:
    content_payload = raw_message.get("content")
    if content_payload is None:
        content_payload = raw_message.get("text")

    return Message(
        id=str(raw_message.get("uuid") or raw_message["id"]),
        participant=_participant_from_role(raw_message.get("sender") or raw_message.get("role")),
        parts=_content_parts_from_payload(content_payload),
        created_at=raw_message.get("created_at"),
        metadata=_as_dict(raw_message.get("metadata")),
    )


def _content_parts_from_payload(payload: Any) -> list[ContentPart]:
    if payload is None:
        return []

    if isinstance(payload, str):
        return [ContentPart(text=payload)]

    if isinstance(payload, list):
        parts: list[ContentPart] = []
        for item in payload:
            parts.extend(_content_parts_from_payload(item))
        return parts

    if isinstance(payload, dict):
        if isinstance(payload.get("parts"), list):
            return _content_parts_from_payload(payload["parts"])

        kind = str(payload.get("type") or payload.get("kind") or "text")
        text = payload.get("text")
        metadata = {
            key: value
            for key, value in payload.items()
            if key not in {"type", "kind", "text", "parts"}
        }
        return [ContentPart(kind=kind, text=text if isinstance(text, str) else None, metadata=metadata)]

    return []


def _participant_from_role(raw_role: Any) -> Participant | None:
    if not isinstance(raw_role, str) or not raw_role:
        return None

    role = raw_role.lower()
    if role == "human":
        role = "user"

    return Participant(id=role, role=role)


def _participants_from_messages(messages: list[Message]) -> list[Participant]:
    participants: list[Participant] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for message in sorted(
        messages,
        key=lambda current: (current.created_at is None, current.created_at),
    ):
        participant = message.participant
        if participant is None:
            continue
        key = (participant.id, participant.role, participant.display_name)
        if key in seen:
            continue
        seen.add(key)
        participants.append(participant)
    return participants


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
