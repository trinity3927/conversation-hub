from __future__ import annotations

import json
from pathlib import Path

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant
from conversation_hub.pipelines import ImportResult
from conversation_hub.storage import conversations_to_list


def test_run_browse_workflow_prompts_for_provider_import_then_browses(tmp_path) -> None:
    from conversation_hub.interactive.workflow import run_browse_workflow

    source_input_path = tmp_path / "chatgpt-export.json"
    source_input_path.write_text("[]", encoding="utf-8")
    output_path = tmp_path / "normalized.json"
    transcript: list[str] = []
    browse_calls: list[list[Conversation]] = []
    import_calls: list[tuple[str, Path]] = []
    commands = iter(["2", "chatgpt", str(source_input_path), str(output_path)])

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    def fake_import(source: str, input_path: Path) -> ImportResult:
        import_calls.append((source, input_path))
        conversations = _workflow_conversations()
        return ImportResult(
            source=source,
            input_path=input_path,
            conversations=conversations,
            conversation_count=len(conversations),
            message_count=sum(len(conversation.messages) for conversation in conversations),
        )

    def fake_browse(
        conversations: list[Conversation],
        input_fn=None,
        output_fn=None,
    ) -> None:
        browse_calls.append(conversations)
        assert input_fn is fake_input
        assert output_fn is fake_output
        output_fn("Browse session opened.")

    run_browse_workflow(
        input_fn=fake_input,
        output_fn=fake_output,
        default_data_dir=tmp_path / "app-data",
        import_runner=fake_import,
        browse_runner=fake_browse,
    )

    assert import_calls == [("chatgpt", source_input_path)]
    assert browse_calls == [_workflow_conversations()]
    assert json.loads(output_path.read_text(encoding="utf-8")) == [
        {
            "id": "conv-imported-1",
            "source": "chatgpt",
            "title": "Imported conversation",
            "participants": [
                {
                    "id": "user",
                    "role": "user",
                    "display_name": None,
                    "metadata": {},
                },
                {
                    "id": "assistant",
                    "role": "assistant",
                    "display_name": None,
                    "metadata": {},
                },
            ],
            "messages": [
                {
                    "id": "msg-1",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Summarize the release plan.", "metadata": {}}],
                    "created_at": "2024-03-09T16:00:01+00:00",
                    "metadata": {},
                },
                {
                    "id": "msg-2",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Here is the release plan.", "metadata": {}}],
                    "created_at": "2024-03-09T16:00:05+00:00",
                    "metadata": {},
                },
            ],
            "created_at": "2024-03-09T16:00:00+00:00",
            "updated_at": "2024-03-09T16:00:05+00:00",
            "tags": ["release"],
            "metadata": {"origin": "test"},
        }
    ]

    combined_output = "\n".join(transcript)
    assert "Choose how to load conversations" in combined_output
    assert "1. Open an existing normalized JSON file" in combined_output
    assert "2. Import from a provider and browse it now" in combined_output
    assert "Choose provider [chatgpt, claude, codex]:" in combined_output
    assert f"Enter the source path for chatgpt:" in combined_output
    assert "Enter normalized output path" in combined_output
    assert f"Imported 1 conversation (2 messages) from chatgpt to {output_path}" in combined_output
    assert "Opening browser for 1 conversation from normalized JSON." in combined_output
    assert "Browse session opened." in combined_output


def test_run_browse_workflow_opens_existing_normalized_json(tmp_path) -> None:
    from conversation_hub.interactive.workflow import run_browse_workflow

    input_path = tmp_path / "normalized.json"
    input_path.write_text(json.dumps(conversations_to_list(_workflow_conversations())), encoding="utf-8")
    transcript: list[str] = []
    browse_calls: list[list[Conversation]] = []
    commands = iter(["1", str(input_path)])

    def fake_input() -> str:
        return next(commands)

    def fake_output(message: object = "") -> None:
        transcript.append(str(message))

    def fake_browse(
        conversations: list[Conversation],
        input_fn=None,
        output_fn=None,
    ) -> None:
        browse_calls.append(conversations)
        assert input_fn is fake_input
        assert output_fn is fake_output
        output_fn("Browse session opened.")

    run_browse_workflow(
        input_fn=fake_input,
        output_fn=fake_output,
        default_data_dir=tmp_path / "app-data",
        browse_runner=fake_browse,
    )

    assert browse_calls == [_workflow_conversations()]

    combined_output = "\n".join(transcript)
    assert "Choose how to load conversations" in combined_output
    assert "Enter normalized JSON path:" in combined_output
    assert "Opening browser for 1 conversation from normalized JSON." in combined_output
    assert "Browse session opened." in combined_output


def _workflow_conversations() -> list[Conversation]:
    return [
        Conversation(
            id="conv-imported-1",
            source="chatgpt",
            title="Imported conversation",
            participants=[
                Participant(id="user", role="user"),
                Participant(id="assistant", role="assistant"),
            ],
            messages=[
                Message(
                    id="msg-1",
                    participant=Participant(id="user", role="user"),
                    parts=[ContentPart(text="Summarize the release plan.")],
                    created_at="2024-03-09T16:00:01+00:00",
                ),
                Message(
                    id="msg-2",
                    participant=Participant(id="assistant", role="assistant"),
                    parts=[ContentPart(text="Here is the release plan.")],
                    created_at="2024-03-09T16:00:05+00:00",
                ),
            ],
            created_at="2024-03-09T16:00:00+00:00",
            updated_at="2024-03-09T16:00:05+00:00",
            tags=["release"],
            metadata={"origin": "test"},
        )
    ]
