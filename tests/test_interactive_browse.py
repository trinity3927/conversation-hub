from __future__ import annotations

from conversation_hub.interactive.browse import run_browse_session
from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


def test_run_browse_session_prints_list_report_details_messages_and_single_analysis() -> None:
    commands = iter(["r", "2", "m", "a", "b", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Conversation browser" in combined_output
    assert "1. Taildrop release checklist" in combined_output
    assert "2. Ops sync" in combined_output
    assert "List command" in combined_output
    assert "Overall report" in combined_output
    assert "Conversations: 2" in combined_output
    assert "Source counts: chatgpt=1, codex=1" in combined_output
    assert "Conversation 2" in combined_output
    assert "ID: conv-2" in combined_output
    assert "Source: codex" in combined_output
    assert "Conversation command" in combined_output
    assert "Messages for conv-2" in combined_output
    assert "1. [user] Check Taildrop access in staging." in combined_output
    assert "2. [assistant] Taildrop staging access is ready." in combined_output
    assert "Analysis report for conversation conv-2" in combined_output
    assert "Conversations: 1" in combined_output
    assert "Quit browser." in combined_output


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
        ),
    ]
