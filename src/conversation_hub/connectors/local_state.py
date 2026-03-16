from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from conversation_hub.connectors.base import Connector
from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


class CodexLocalStateConnector(Connector):
    source_name = "codex"

    def __init__(self, input_path: str | Path) -> None:
        self.input_path = Path(input_path)

    def fetch(self) -> Iterable[Conversation]:
        for session_path in _iter_codex_session_paths(self.input_path):
            yield _conversation_from_codex_session(session_path)


def _iter_codex_session_paths(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    if not input_path.is_dir():
        raise ValueError(f"Unsupported Codex input path: {input_path}")

    if input_path.name == ".codex":
        search_root = input_path / "sessions"
    elif input_path.name == "sessions":
        search_root = input_path
    elif (input_path / "sessions").is_dir():
        search_root = input_path / "sessions"
    else:
        search_root = input_path

    return sorted(path for path in search_root.rglob("*.jsonl") if path.is_file())


def _conversation_from_codex_session(session_path: Path) -> Conversation:
    events = list(_load_jsonl_records(session_path))
    session_meta = _first_payload_for_event_type(events, "session_meta")
    session_id = str(session_meta.get("id") or session_path.stem)

    messages: list[Message] = []
    first_user_text: str | None = None

    for event in events:
        message = _message_from_event(event, session_id, len(messages) + 1)
        if message is None:
            continue
        messages.append(message)
        if message.role == "user" and first_user_text is None and message.text_content.strip():
            first_user_text = message.text_content.strip()

    created_at = session_meta.get("timestamp") or (messages[0].created_at if messages else None)
    updated_at = messages[-1].created_at if messages else created_at

    return Conversation(
        id=session_id,
        source=CodexLocalStateConnector.source_name,
        title=first_user_text,
        participants=_participants_from_messages(messages),
        messages=messages,
        created_at=created_at,
        updated_at=updated_at,
        metadata={"codex": _codex_conversation_metadata(session_meta, session_path)},
    )


def _message_from_event(event: dict[str, Any], session_id: str, message_index: int) -> Message | None:
    if event.get("type") != "response_item":
        return None

    payload = _as_dict(event.get("payload"))
    if payload.get("type") != "message":
        return None

    participant = _participant_from_role(payload.get("role"))
    if participant is None:
        return None

    parts, content_types = _content_parts_from_codex_content(payload.get("content"))
    if not parts:
        return None

    metadata: dict[str, Any] = {}
    if content_types:
        metadata["codex_content_types"] = content_types

    return Message(
        id=f"{session_id}-message-{message_index}",
        participant=participant,
        parts=parts,
        created_at=event.get("timestamp"),
        metadata=metadata,
    )


def _content_parts_from_codex_content(payload: Any) -> tuple[list[ContentPart], list[str]]:
    if isinstance(payload, str):
        return [ContentPart(text=payload)], ["text"]

    if not isinstance(payload, list):
        return [], []

    parts: list[ContentPart] = []
    content_types: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if isinstance(item_type, str):
            content_types.append(item_type)
        text = item.get("text")
        if not isinstance(text, str):
            continue
        kind = "text" if item_type in {None, "input_text", "output_text"} else str(item_type)
        parts.append(ContentPart(kind=kind, text=text))

    return parts, content_types


def _participant_from_role(raw_role: Any) -> Participant | None:
    if not isinstance(raw_role, str) or raw_role not in {"user", "assistant"}:
        return None
    return Participant(id=raw_role, role=raw_role)


def _participants_from_messages(messages: list[Message]) -> list[Participant]:
    participants: list[Participant] = []
    seen: set[str] = set()
    for message in messages:
        if message.participant is None or message.participant.role is None:
            continue
        if message.participant.role in seen:
            continue
        seen.add(message.participant.role)
        participants.append(message.participant)
    return participants


def _codex_conversation_metadata(session_meta: dict[str, Any], session_path: Path) -> dict[str, Any]:
    metadata = {"session_file": str(session_path)}

    field_mapping = {
        "cwd": "cwd",
        "cli_version": "cli_version",
        "model_provider": "model_provider",
        "source": "session_source",
    }
    for source_field, target_field in field_mapping.items():
        value = session_meta.get(source_field)
        if value is not None:
            metadata[target_field] = value

    return metadata


def _first_payload_for_event_type(events: list[dict[str, Any]], event_type: str) -> dict[str, Any]:
    for event in events:
        if event.get("type") == event_type:
            return _as_dict(event.get("payload"))
    return {}


def _load_jsonl_records(path: Path) -> Iterable[dict[str, Any]]:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        record = json.loads(raw_line)
        if isinstance(record, dict):
            yield record


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}
