from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from conversation_hub.models.schema import Conversation


class Connector(ABC):
    source_name: str

    @abstractmethod
    def fetch(self) -> Iterable[Conversation]:
        """Return normalized conversations from a source."""
