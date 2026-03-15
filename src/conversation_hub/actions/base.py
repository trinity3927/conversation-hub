from __future__ import annotations

from abc import ABC, abstractmethod

from conversation_hub.models.schema import Conversation


class Action(ABC):
    name: str

    @abstractmethod
    def run(self, conversation: Conversation) -> None:
        """Run a post-processing action for a normalized conversation."""
