from __future__ import annotations

import json
from pathlib import Path

from conversation_hub.models.schema import ContentPart, Conversation, Message, Participant
from conversation_hub.pipelines import ImportResult
from conversation_hub.storage import conversations_to_list, write_conversations_sqlite


def test_run_browse_workflow_renders_home_screen_with_recent_datasets_and_defaults(tmp_path) -> None:
    from conversation_hub.interactive.workflow import run_browse_workflow

    input_path = tmp_path / "normalized.json"
    input_path.write_text(json.dumps(conversations_to_list(_workflow_conversations())), encoding="utf-8")
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "last_browse_filter": "ops",
                "last_provider_import_paths": {"claude": str(tmp_path / "claude-export")},
                "recent_datasets": [
                    {
                        "kind": "normalized_json",
                        "label": "Normalized sample",
                        "path": str(input_path),
                        "provider": None,
                        "conversation_count": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    transcript: list[str] = []
    browse_calls: list[list[Conversation]] = []
    commands = iter(["1"])

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
        state_path=state_path,
        browse_runner=fake_browse,
    )

    assert browse_calls == [_workflow_conversations()]

    combined_output = "\n".join(transcript)
    assert "Conversation Hub" in combined_output
    assert "Minimal home" in combined_output
    assert "Recent datasets" in combined_output
    assert "1. Normalized sample" in combined_output
    assert "normalized_json | 1 conversation" in combined_output
    assert "Remembered defaults" in combined_output
    assert "Last browse filter: ops" in combined_output
    assert f"claude: {tmp_path / 'claude-export'}" in combined_output
    assert "Quick actions" in combined_output
    assert "i import provider export" in combined_output
    assert "j open normalized JSON" in combined_output
    assert "s open local SQLite export" in combined_output
    assert "Home command [recent number, i, j, s, q]:" in combined_output
    assert "Opening browser for 1 conversation from normalized JSON." in combined_output
    assert "Browse session opened." in combined_output


def test_run_browse_workflow_remembers_provider_path_and_autodetects_claude_folder_export(tmp_path) -> None:
    from conversation_hub.interactive.workflow import run_browse_workflow

    export_dir = tmp_path / "claude-export"
    export_dir.mkdir()
    detected_export_path = export_dir / "conversations.json"
    detected_export_path.write_text(
        json.dumps(
            {
                "conversations": [
                    {
                        "uuid": "claude-conv-1",
                        "name": "Release summary",
                        "messages": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    transcript: list[str] = []
    browse_calls: list[list[Conversation]] = []
    import_calls: list[tuple[str, Path]] = []
    state_path = tmp_path / "state.json"
    commands = iter(["i", "claude", str(export_dir), ""])

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
        output_fn("Browse session opened.")

    run_browse_workflow(
        input_fn=fake_input,
        output_fn=fake_output,
        state_path=state_path,
        default_data_dir=tmp_path / "app-data",
        import_runner=fake_import,
        browse_runner=fake_browse,
    )

    assert import_calls == [("claude", detected_export_path)]
    assert browse_calls == [_workflow_conversations()]

    saved_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved_state["last_provider_import_paths"]["claude"] == str(export_dir)
    assert saved_state["recent_datasets"][0]["path"] == str(tmp_path / "app-data" / "claude.json")
    assert saved_state["recent_datasets"][0]["provider"] == "claude"
    assert saved_state["recent_datasets"][0]["kind"] == "normalized_json"

    combined_output = "\n".join(transcript)
    assert "Choose provider [chatgpt, claude, codex]:" in combined_output
    assert "Enter source path for claude:" in combined_output
    assert f"Detected Claude export file: {detected_export_path}" in combined_output
    assert "Enter normalized output path" in combined_output
    assert "Imported 1 conversation (2 messages) from claude" in combined_output
    assert "Opening browser for 1 conversation from normalized JSON." in combined_output


def test_run_browse_workflow_uses_remembered_provider_path_as_default(tmp_path) -> None:
    from conversation_hub.interactive.workflow import run_browse_workflow

    remembered_codex_path = tmp_path / ".codex"
    remembered_codex_path.mkdir()
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "last_browse_filter": None,
                "last_provider_import_paths": {"codex": str(remembered_codex_path)},
                "recent_datasets": [],
            }
        ),
        encoding="utf-8",
    )
    transcript: list[str] = []
    import_calls: list[tuple[str, Path]] = []
    commands = iter(["i", "codex", "", ""])

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

    run_browse_workflow(
        input_fn=fake_input,
        output_fn=fake_output,
        state_path=state_path,
        default_data_dir=tmp_path / "app-data",
        import_runner=fake_import,
        browse_runner=lambda conversations, input_fn=None, output_fn=None: None,
    )

    assert import_calls == [("codex", remembered_codex_path)]

    combined_output = "\n".join(transcript)
    assert f"Enter source path for codex [default: {remembered_codex_path}]:" in combined_output


def test_run_browse_workflow_opens_existing_sqlite_export_and_registers_it(tmp_path) -> None:
    from conversation_hub.interactive.workflow import run_browse_workflow

    input_path = tmp_path / "conversations.db"
    write_conversations_sqlite(_workflow_conversations(), input_path)
    state_path = tmp_path / "state.json"
    transcript: list[str] = []
    browse_calls: list[list[Conversation]] = []
    commands = iter(["s", str(input_path)])

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
        output_fn("Browse session opened.")

    run_browse_workflow(
        input_fn=fake_input,
        output_fn=fake_output,
        state_path=state_path,
        browse_runner=fake_browse,
    )

    assert browse_calls == [_workflow_conversations()]

    saved_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert saved_state["recent_datasets"][0]["kind"] == "sqlite_export"
    assert saved_state["recent_datasets"][0]["path"] == str(input_path)

    combined_output = "\n".join(transcript)
    assert "Enter SQLite export path:" in combined_output
    assert "Opening browser for 1 conversation from SQLite export." in combined_output
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
