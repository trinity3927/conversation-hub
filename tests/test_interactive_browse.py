from __future__ import annotations

from conversation_hub.interactive.browse import run_browse_session
from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant


def test_run_browse_session_prints_structured_cards_status_and_metadata() -> None:
    commands = iter(["2", "t", "m", "a", "b", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Conversation Browser" in combined_output
    assert "Mode: browse list" in combined_output
    assert "Dataset summary: 2 conversations | 6 messages | chatgpt=1, claude=1" in combined_output
    assert "View: showing 1-2 of 2 | page 1/1" in combined_output
    assert "1. Taildrop release checklist" in combined_output
    assert "chatgpt | 3 msgs | updated 2024-03-11T08:05:00+00:00" in combined_output
    assert "preview: Draft a Taildrop release checklist and keep the output deterministic." in combined_output
    assert "tasks: draft release checklist; summarize rollout blockers" in combined_output
    assert "artifacts: docs/release.md, https://taildrop.dev/checklist" in combined_output
    assert "2. Ops sync" in combined_output
    assert "claude | 3 msgs | updated 2024-03-10T09:05:00+00:00" in combined_output
    assert "Legend: [number open] [n next] [p prev] [f filter] [/ search] [r report] [q quit]" in combined_output
    assert "List command [number, n, p, f, /, r, q]:" in combined_output
    assert "Mode: conversation detail" in combined_output
    assert "Conversation 2 of 2" in combined_output
    assert "ID: conv-2" in combined_output
    assert "Source: claude" in combined_output
    assert "Operators: [m messages] [a report] [t metadata] [b back] [q quit]" in combined_output
    assert "Conversation metadata" in combined_output
    assert "Tags: ops, staging" in combined_output
    assert "Metadata: origin=test" in combined_output
    assert "Messages for conv-2" in combined_output
    assert "1. [user] Check Taildrop access in staging and capture follow-ups." in combined_output
    assert "Analysis report for conversation conv-2" in combined_output
    assert "Quick summary" in combined_output
    assert "Likely tasks" in combined_output
    assert "Quit browser." in combined_output


def test_run_browse_session_supports_filter_and_interactive_search_without_collapsing_the_list() -> None:
    commands = iter(["f", "ops", "/", "release", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Enter filter keyword [blank clears]:" in combined_output
    assert "Active filter: ops" in combined_output
    assert "Showing 1 conversation after filter." in combined_output
    assert "Enter search query [blank clears]:" in combined_output
    assert "Active search: release (0 matches in current filtered view)" in combined_output
    assert "View: showing 1-1 of 1 | page 1/1" in combined_output
    assert "Legend: [number open] [n next] [p prev] [f filter] [/ search] [r report] [q quit]" in combined_output
    assert "Quit browser." in combined_output


def test_run_browse_session_uses_pagination_for_large_datasets() -> None:
    commands = iter(["n", "p", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_many_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "View: showing 1-8 of 11 | page 1/2" in combined_output
    assert "View: showing 9-11 of 11 | page 2/2" in combined_output
    assert "1. Dataset conversation 11" in combined_output
    assert "3. Dataset conversation 1" in combined_output
    assert "Legend: [number open] [n next] [p prev] [f filter] [/ search] [r report] [q quit]" in combined_output
    assert "Quit browser." in combined_output


def test_run_browse_session_report_focuses_on_high_signal_sections() -> None:
    commands = iter(["r", "q"])
    transcript: list[str] = []

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    run_browse_session(_browseable_conversations(), input_fn=fake_input, output_fn=fake_output)

    combined_output = "\n".join(transcript)

    assert "Overall report" in combined_output
    assert "Quick summary" in combined_output
    assert "Repeated constraints/preferences" in combined_output
    assert "Likely tasks" in combined_output
    assert "Unresolved asks" in combined_output
    assert "Artifacts" in combined_output
    assert "Source comparison" in combined_output
    assert "Important entities" not in combined_output
    assert "Reusable prompts" not in combined_output
    assert "Source patterns" not in combined_output
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
                    parts=[
                        ContentPart(
                            text=(
                                "Draft a Taildrop release checklist and keep the output deterministic. "
                                "Capture notes in docs/release.md."
                            )
                        )
                    ],
                    created_at="2024-03-11T08:00:01Z",
                ),
                Message(
                    id="conv-1-msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Here is the checklist. It references https://taildrop.dev/checklist.")],
                    created_at="2024-03-11T08:00:05Z",
                ),
                Message(
                    id="conv-1-msg-3",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Summarize rollout blockers before launch.")],
                    created_at="2024-03-11T08:04:05Z",
                ),
            ],
            created_at="2024-03-11T08:00:00Z",
            updated_at="2024-03-11T08:05:00Z",
            metadata={"origin": "seed"},
        ),
        Conversation(
            id="conv-2",
            source="claude",
            title="Ops sync",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="conv-2-msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Check Taildrop access in staging and capture follow-ups.")],
                    created_at="2024-03-10T09:00:01Z",
                ),
                Message(
                    id="conv-2-msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Taildrop staging access is ready. Update staging-access.md.")],
                    created_at="2024-03-10T09:00:05Z",
                ),
                Message(
                    id="conv-2-msg-3",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Prefer a concise handoff and note unresolved asks for the next shift.")],
                    created_at="2024-03-10T09:03:05Z",
                ),
            ],
            created_at="2024-03-10T09:00:00Z",
            updated_at="2024-03-10T09:05:00Z",
            tags=["ops", "staging"],
            metadata={"origin": "test"},
        ),
    ]


def _many_conversations() -> list[Conversation]:
    conversations: list[Conversation] = []
    for index in range(1, 12):
        conversations.append(
            Conversation(
                id=f"conv-{index}",
                source="chatgpt" if index % 2 else "claude",
                title=f"Dataset conversation {index}",
                participants=[
                    Participant(id="user", role="user"),
                    Participant(id="assistant", role="assistant"),
                ],
                messages=[
                    Message(
                        id=f"msg-{index}",
                        participant=Participant(id="user", role="user"),
                        parts=[ContentPart(text=f"Summarize release item {index}.")],
                        created_at=f"2024-03-{index:02d}T08:00:00Z",
                    )
                ],
                created_at=f"2024-03-{index:02d}T08:00:00Z",
                updated_at=f"2024-03-{index:02d}T09:00:00Z",
            )
        )
    return conversations
