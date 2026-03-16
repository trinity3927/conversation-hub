from __future__ import annotations

import json
import sqlite3

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


def test_import_command_writes_normalized_codex_json(tmp_path, capsys) -> None:
    codex_root = tmp_path / ".codex"
    session_path = codex_root / "sessions" / "2026" / "03" / "16" / "rollout-session.jsonl"
    session_path.parent.mkdir(parents=True)
    session_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-03-16T02:15:14.189Z",
                        "type": "session_meta",
                        "payload": {
                            "id": "session-1",
                            "timestamp": "2026-03-16T02:15:14.189Z",
                            "cwd": "/home/sindri/taildrop",
                            "cli_version": "0.114.0",
                            "source": "cli",
                            "model_provider": "openai",
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-03-16T02:15:59.708Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "Check Taildrop config."}],
                        },
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-03-16T02:16:24.332Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "Taildrop is enabled."}],
                        },
                    }
                ),
            ]
        )
        + "\n"
    )
    output_path = tmp_path / "normalized.json"

    exit_code = main(
        [
            "import",
            "--source",
            "codex",
            "--input",
            str(codex_root),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text())
    assert payload == [
        {
            "id": "session-1",
            "source": "codex",
            "title": "Check Taildrop config.",
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
                    "id": "session-1-message-1",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Check Taildrop config.", "metadata": {}}],
                    "created_at": "2026-03-16T02:15:59.708000+00:00",
                    "metadata": {"codex_content_types": ["input_text"]},
                },
                {
                    "id": "session-1-message-2",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Taildrop is enabled.", "metadata": {}}],
                    "created_at": "2026-03-16T02:16:24.332000+00:00",
                    "metadata": {"codex_content_types": ["output_text"]},
                },
            ],
            "created_at": "2026-03-16T02:15:14.189000+00:00",
            "updated_at": "2026-03-16T02:16:24.332000+00:00",
            "tags": [],
            "metadata": {
                "codex": {
                    "cwd": "/home/sindri/taildrop",
                    "cli_version": "0.114.0",
                    "model_provider": "openai",
                    "session_source": "cli",
                    "session_file": str(session_path),
                }
            },
        }
    ]
    assert capsys.readouterr().out.strip() == f"Imported 1 conversation (2 messages) from codex to {output_path}"


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


def test_analyze_command_writes_analysis_report(tmp_path, capsys) -> None:
    input_path = tmp_path / "normalized.json"
    output_path = tmp_path / "analysis.json"
    input_path.write_text(
        json.dumps(
            [
                {
                    "id": "conv-1",
                    "source": "chatgpt",
                    "title": "Taildrop release checklist",
                    "participants": [
                        {"id": "user", "role": "user", "display_name": None, "metadata": {}},
                        {"id": "assistant", "role": "assistant", "display_name": None, "metadata": {}},
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
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": "Draft a Taildrop release checklist. Keep it deterministic.",
                                    "metadata": {},
                                }
                            ],
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
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": "Here is the Taildrop release checklist.",
                                    "metadata": {},
                                }
                            ],
                            "created_at": "2024-03-09T16:00:05+00:00",
                            "metadata": {},
                        },
                    ],
                    "created_at": "2024-03-09T16:00:00+00:00",
                    "updated_at": "2024-03-09T16:00:05+00:00",
                    "tags": [],
                    "metadata": {},
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "analyze",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(output_path.read_text())
    assert report["summary"] == {
        "conversation_count": 1,
        "message_count": 2,
        "source_counts": {"chatgpt": 1},
    }
    assert set(report) == {
        "summary",
        "source_patterns",
        "recurring_projects_goals",
        "important_entities",
        "reusable_prompts",
        "repeated_preferences_constraints",
        "unresolved_threads",
    }
    assert capsys.readouterr().out.strip() == (
        f"Analyzed 1 conversation (2 messages) from {input_path} to {output_path}"
    )


def test_export_command_writes_sqlite_database(tmp_path, capsys) -> None:
    input_path = tmp_path / "normalized.json"
    output_path = tmp_path / "conversations.db"
    input_path.write_text(
        json.dumps(
            [
                {
                    "id": "conv-1",
                    "source": "chatgpt",
                    "title": "Taildrop release checklist",
                    "participants": [
                        {"id": "user", "role": "user", "display_name": None, "metadata": {}},
                        {"id": "assistant", "role": "assistant", "display_name": None, "metadata": {}},
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
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": "Draft a Taildrop release checklist.",
                                    "metadata": {},
                                }
                            ],
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
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": "Here is the checklist.",
                                    "metadata": {},
                                }
                            ],
                            "created_at": "2024-03-09T16:00:05+00:00",
                            "metadata": {},
                        },
                    ],
                    "created_at": "2024-03-09T16:00:00+00:00",
                    "updated_at": "2024-03-09T16:00:05+00:00",
                    "tags": [],
                    "metadata": {},
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "export",
            "--format",
            "sqlite",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()

    connection = sqlite3.connect(output_path)
    try:
        assert connection.execute("SELECT COUNT(*) FROM conversations").fetchone() == (1,)
        assert connection.execute("SELECT COUNT(*) FROM messages").fetchone() == (2,)
    finally:
        connection.close()

    assert capsys.readouterr().out.strip() == (
        f"Exported 1 conversation (2 messages) from {input_path} to {output_path} as sqlite"
    )
