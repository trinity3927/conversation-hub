from __future__ import annotations

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant
from conversation_hub.storage import write_conversations_sqlite
from conversation_hub.storage.sqlite_search import (
    SQLiteSearchMatch,
    SQLiteSearchResults,
    load_conversations_sqlite,
    search_conversations_sqlite,
)


def test_search_conversations_sqlite_returns_deterministic_matches_with_metadata(tmp_path) -> None:
    output_path = tmp_path / "conversations.db"
    write_conversations_sqlite(_sample_conversations(), output_path)

    result = search_conversations_sqlite(output_path, query="taildrop")

    assert result == SQLiteSearchResults(
        query="taildrop",
        limit=10,
        result_count=2,
        results=[
            SQLiteSearchMatch(
                source="chatgpt",
                conversation_id="conv-title",
                title="Taildrop release checklist",
                message_count=2,
                excerpt="Taildrop release checklist",
            ),
            SQLiteSearchMatch(
                source="claude",
                conversation_id="conv-text",
                title="Roadmap review",
                message_count=2,
                excerpt="Document the Taildrop migration plan and list blockers.",
            ),
        ],
    )


def test_search_conversations_sqlite_respects_limit(tmp_path) -> None:
    output_path = tmp_path / "conversations.db"
    write_conversations_sqlite(_sample_conversations(), output_path)

    result = search_conversations_sqlite(output_path, query="taildrop", limit=1)

    assert result.result_count == 1
    assert result.results == [
        SQLiteSearchMatch(
            source="chatgpt",
            conversation_id="conv-title",
            title="Taildrop release checklist",
            message_count=2,
            excerpt="Taildrop release checklist",
        )
    ]


def test_load_conversations_sqlite_round_trips_conversation_structure(tmp_path) -> None:
    output_path = tmp_path / "conversations.db"
    write_conversations_sqlite(_sample_conversations(), output_path)

    loaded = load_conversations_sqlite(output_path)

    assert loaded == [
        Conversation(
            id="conv-other",
            source="codex",
            title="Infra cleanup",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Remove stale worktrees.")],
                    created_at="2024-03-11T11:00:01Z",
                )
            ],
            created_at="2024-03-11T11:00:00Z",
            updated_at="2024-03-11T11:00:01Z",
            tags=[],
            metadata={},
        ),
        Conversation(
            id="conv-text",
            source="claude",
            title="Roadmap review",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Document the Taildrop migration plan and list blockers.")],
                    created_at="2024-03-10T09:00:01Z",
                ),
                Message(
                    id="msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Blockers are the final review and rollout sign-off.")],
                    created_at="2024-03-10T09:00:05Z",
                ),
            ],
            created_at="2024-03-10T09:00:00Z",
            updated_at="2024-03-10T09:00:05Z",
            tags=[],
            metadata={},
        ),
        Conversation(
            id="conv-title",
            source="chatgpt",
            title="Taildrop release checklist",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Make the rollout deterministic.")],
                    created_at="2024-03-09T16:00:01Z",
                ),
                Message(
                    id="msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Start with staged deployment.")],
                    created_at="2024-03-09T16:00:05Z",
                ),
            ],
            created_at="2024-03-09T16:00:00Z",
            updated_at="2024-03-09T16:05:00Z",
            tags=[],
            metadata={},
        ),
    ]


def _sample_conversations() -> list[Conversation]:
    return [
        Conversation(
            id="conv-title",
            source="chatgpt",
            title="Taildrop release checklist",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Make the rollout deterministic.")],
                    created_at="2024-03-09T16:00:01Z",
                ),
                Message(
                    id="msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Start with staged deployment.")],
                    created_at="2024-03-09T16:00:05Z",
                ),
            ],
            created_at="2024-03-09T16:00:00Z",
            updated_at="2024-03-09T16:05:00Z",
        ),
        Conversation(
            id="conv-text",
            source="claude",
            title="Roadmap review",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Document the Taildrop migration plan and list blockers.")],
                    created_at="2024-03-10T09:00:01Z",
                ),
                Message(
                    id="msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Blockers are the final review and rollout sign-off.")],
                    created_at="2024-03-10T09:00:05Z",
                ),
            ],
            created_at="2024-03-10T09:00:00Z",
            updated_at="2024-03-10T09:00:05Z",
        ),
        Conversation(
            id="conv-other",
            source="codex",
            title="Infra cleanup",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Remove stale worktrees.")],
                    created_at="2024-03-11T11:00:01Z",
                )
            ],
            created_at="2024-03-11T11:00:00Z",
            updated_at="2024-03-11T11:00:01Z",
        ),
    ]
