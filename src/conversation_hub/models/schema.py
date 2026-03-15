from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


TimestampInput = datetime | int | float | str | None


def normalize_timestamp(value: TimestampInput) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if isinstance(value, str):
        normalized_value = value.strip()
        if not normalized_value:
            return None
        if normalized_value.endswith("Z"):
            normalized_value = f"{normalized_value[:-1]}+00:00"
        return normalize_timestamp(datetime.fromisoformat(normalized_value))

    raise TypeError(f"Unsupported timestamp value: {value!r}")


@dataclass(slots=True)
class Participant:
    id: str | None = None
    role: str | None = None
    display_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ContentPart:
    kind: str = "text"
    text: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Message:
    id: str
    participant: Participant | None = None
    parts: list[ContentPart] = field(default_factory=list)
    created_at: TimestampInput = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.created_at = normalize_timestamp(self.created_at)

    @property
    def role(self) -> str | None:
        return None if self.participant is None else self.participant.role

    @property
    def text_content(self) -> str:
        return "".join(part.text for part in self.parts if part.text)

    @property
    def content(self) -> str:
        return self.text_content


@dataclass(slots=True)
class Conversation:
    id: str
    source: str
    title: str | None = None
    participants: list[Participant] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)
    created_at: TimestampInput = None
    updated_at: TimestampInput = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.created_at = normalize_timestamp(self.created_at)
        self.updated_at = normalize_timestamp(self.updated_at)

    def messages_in_chronological_order(self) -> list[Message]:
        last_possible_timestamp = datetime.max.replace(tzinfo=timezone.utc)
        return sorted(
            self.messages,
            key=lambda message: (
                message.created_at is None,
                message.created_at or last_possible_timestamp,
            ),
        )
