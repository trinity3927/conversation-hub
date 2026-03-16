from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from conversation_hub.connectors import get_connector_class
from conversation_hub.models.schema import Conversation


@dataclass(slots=True)
class ImportResult:
    source: str
    input_path: Path
    conversations: list[Conversation]
    conversation_count: int
    message_count: int


def run_import(source: str, input_path: str | Path) -> ImportResult:
    normalized_input_path = Path(input_path)
    connector_class = get_connector_class(source)
    conversations = list(connector_class(normalized_input_path).fetch())
    return ImportResult(
        source=source,
        input_path=normalized_input_path,
        conversations=conversations,
        conversation_count=len(conversations),
        message_count=sum(len(conversation.messages) for conversation in conversations),
    )
