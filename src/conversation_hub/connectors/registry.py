from __future__ import annotations

from conversation_hub.connectors.base import Connector
from conversation_hub.connectors.file_exports import (
    ChatGPTExportConnector,
    ClaudeExportConnector,
)
from conversation_hub.connectors.local_state import CodexLocalStateConnector


CONNECTOR_REGISTRY: dict[str, type[Connector]] = {
    ChatGPTExportConnector.source_name: ChatGPTExportConnector,
    ClaudeExportConnector.source_name: ClaudeExportConnector,
    CodexLocalStateConnector.source_name: CodexLocalStateConnector,
}


def available_sources() -> list[str]:
    return sorted(CONNECTOR_REGISTRY)


def get_connector_class(source: str) -> type[Connector]:
    try:
        return CONNECTOR_REGISTRY[source]
    except KeyError as exc:
        raise ValueError(f"Unsupported connector source: {source}") from exc
