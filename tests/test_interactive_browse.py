from __future__ import annotations

from conversation_hub.interactive.browse import run_browse_session
from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


def test_run_browse_session_prints_guided_views_previews_and_metadata() -> None:
    commands = iter(["2", "t", "m", "a", "b", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Conversation Browser" in combined_output
    assert "Loaded conversations: 2" in combined_output
    assert "Conversation list" in combined_output
    assert "1. Taildrop release checklist" in combined_output
    assert "source: chatgpt" in combined_output
    assert "messages: 2" in combined_output
    assert "preview: Draft a Taildrop release checklist." in combined_output
    assert "2. Ops sync" in combined_output
    assert "preview: Check Taildrop access in staging." in combined_output
    assert "Main commands" in combined_output
    assert "[number] open conversation" in combined_output
    assert "r overall report for current view" in combined_output
    assert "f filter conversations by keyword" in combined_output
    assert "q quit browser" in combined_output
    assert "List command" in combined_output
    assert "Conversation 2 of 2" in combined_output
    assert "ID: conv-2" in combined_output
    assert "Source: codex" in combined_output
    assert "Conversation commands" in combined_output
    assert "m show messages" in combined_output
    assert "a analysis report" in combined_output
    assert "t metadata and tags" in combined_output
    assert "b back to conversation list" in combined_output
    assert "q quit browser" in combined_output
    assert "Conversation command" in combined_output
    assert "Conversation metadata" in combined_output
    assert "Tags: ops, staging" in combined_output
    assert "Metadata: origin=test" in combined_output
    assert "Messages for conv-2" in combined_output
    assert "1. [user] Check Taildrop access in staging." in combined_output
    assert "2. [assistant] Taildrop staging access is ready." in combined_output
    assert "Analysis report for conversation conv-2" in combined_output
    assert "Conversations: 1" in combined_output
    assert "Quit browser." in combined_output


def test_run_browse_session_filters_conversations_by_keyword() -> None:
    commands = iter(["f", "ops", "1", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Main commands" in combined_output
    assert "List command [number, r, f, q]:" in combined_output
    assert "Enter filter keyword [blank clears]:" in combined_output
    assert "Showing 1 conversation matching 'ops'." in combined_output
    assert "Active filter: ops" in combined_output
    assert "Conversation 1 of 1" in combined_output
    assert "ID: conv-2" in combined_output
    assert "Quit browser." in combined_output


def test_run_browse_session_report_omits_low_value_top_keyword_noise() -> None:
    commands = iter(["r", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Overall report" in combined_output
    assert "Source patterns" in combined_output
    assert "chatgpt: conversations=1, messages=2" in combined_output
    assert "codex: conversations=1, messages=2" in combined_output
    assert "top_keywords" not in combined_output


def _browseable_conversations() -> list[Conversation]:
    return [
        Conversation(
            id="conv-1",
            source="chatgpt",
            title="Taildrop release checklist",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="conv-1-msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Draft a Taildrop release checklist.")],
                    created_at="2024-03-11T08:00:01Z",
                ),
                Message(
                    id="conv-1-msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Here is the checklist.")],
                    created_at="2024-03-11T08:00:05Z",
                ),
            ],
            created_at="2024-03-11T08:00:00Z",
            updated_at="2024-03-11T08:05:00Z",
            metadata={"origin": "seed"},
        ),
        Conversation(
            id="conv-2",
            source="codex",
            title="Ops sync",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="conv-2-msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Check Taildrop access in staging.")],
                    created_at="2024-03-10T09:00:01Z",
                ),
                Message(
                    id="conv-2-msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Taildrop staging access is ready.")],
                    created_at="2024-03-10T09:00:05Z",
                ),
            ],
            created_at="2024-03-10T09:00:00Z",
            updated_at="2024-03-10T09:05:00Z",
            tags=["ops", "staging"],
            metadata={"origin": "test"},
        ),
    ]
