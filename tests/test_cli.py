from __future__ import annotations

import json

import pytest

from conversation_hub.cli import main


def test_import_command_writes_normalized_chatgpt_json(tmp_path, capsys) -> None:
    input_path = tmp_path / "conversations.json"
    output_path = tmp_path / "normalized.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "id": "chatgpt-conv-1",
                    "title": "Tokyo ideas",
                    "create_time": 1710000000,
                    "update_time": 1710000300,
                    "mapping": {
                        "node-user": {
                            "id": "node-user",
                            "message": {
                                "id": "msg-user",
                                "author": {"role": "user"},
                                "create_time": 1710000001,
                                "content": {
                                    "content_type": "text",
                                    "parts": ["Plan me a trip to Tokyo."],
                                },
                            },
                        },
                        "node-assistant": {
                            "id": "node-assistant",
                            "message": {
                                "id": "msg-assistant",
                                "author": {"role": "assistant"},
                                "create_time": 1710000005,
                                "content": {
                                    "content_type": "text",
                                    "parts": ["Start with Shinjuku."],
                                },
                                "metadata": {"model_slug": "gpt-4o-mini"},
                            },
                        },
                    },
                }
            ]
        )
    )

    exit_code = main(
        [
            "import",
            "--source",
            "chatgpt",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert json.loads(output_path.read_text()) == [
        {
            "id": "chatgpt-conv-1",
            "source": "chatgpt",
            "title": "Tokyo ideas",
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
                    "id": "msg-user",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Plan me a trip to Tokyo.", "metadata": {}}],
                    "created_at": "2024-03-09T16:00:01+00:00",
                    "metadata": {},
                },
                {
                    "id": "msg-assistant",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Start with Shinjuku.", "metadata": {}}],
                    "created_at": "2024-03-09T16:00:05+00:00",
                    "metadata": {"model_slug": "gpt-4o-mini"},
                },
            ],
            "created_at": "2024-03-09T16:00:00+00:00",
            "updated_at": "2024-03-09T16:05:00+00:00",
            "tags": [],
            "metadata": {},
        }
    ]
    assert capsys.readouterr().out.strip() == (
        f"Imported 1 conversation (2 messages) from chatgpt to {output_path}"
    )


def test_import_command_writes_normalized_claude_json(tmp_path, capsys) -> None:
    input_path = tmp_path / "claude-export.json"
    output_path = tmp_path / "normalized.json"
    input_path.write_text(
        json.dumps(
            {
                "conversations": [
                    {
                        "uuid": "claude-conv-1",
                        "name": "Release summary",
                        "created_at": "2024-05-01T10:00:00Z",
                        "updated_at": "2024-05-01T10:05:00Z",
                        "messages": [
                            {
                                "uuid": "claude-msg-1",
                                "sender": "human",
                                "text": "Summarize these commits.",
                                "created_at": "2024-05-01T10:00:10Z",
                            },
                            {
                                "uuid": "claude-msg-2",
                                "sender": "assistant",
                                "content": [
                                    {"type": "text", "text": "Here is the summary."},
                                    {"type": "text", "text": " It covers three changes."},
                                ],
                                "created_at": "2024-05-01T10:00:20Z",
                            },
                        ],
                    }
                ]
            }
        )
    )

    exit_code = main(
        [
            "import",
            "--source",
            "claude",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text())
    assert payload[0]["id"] == "claude-conv-1"
    assert payload[0]["source"] == "claude"
    assert [message["id"] for message in payload[0]["messages"]] == [
        "claude-msg-1",
        "claude-msg-2",
    ]
    assert payload[0]["messages"][0]["participant"]["role"] == "user"
    assert payload[0]["messages"][1]["parts"] == [
        {"kind": "text", "text": "Here is the summary.", "metadata": {}},
        {"kind": "text", "text": " It covers three changes.", "metadata": {}},
    ]
    assert capsys.readouterr().out.strip() == (
        f"Imported 1 conversation (2 messages) from claude to {output_path}"
    )


def test_import_command_rejects_unsupported_sources(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "import",
                "--source",
                "discord",
                "--input",
                "input.json",
                "--output",
                "output.json",
            ]
        )

    assert excinfo.value.code == 2
    stderr = capsys.readouterr().err
    assert "invalid choice" in stderr
    assert "discord" in stderr
