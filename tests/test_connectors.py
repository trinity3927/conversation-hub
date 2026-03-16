from __future__ import annotations

import json
from datetime import datetime, timezone

from conversation_hub.connectors import (
    ClaudeExportConnector,
    ChatGPTExportConnector,
    CodexLocalStateConnector,
)


def test_chatgpt_export_connector_parses_conversations_json(tmp_path) -> None:
    export_path = tmp_path / "conversations.json"
    export_path.write_text(
        json.dumps(
            [
                {
                    "id": "chatgpt-conv-1",
                    "title": "Tokyo ideas",
                    "create_time": 1710000000,
                    "update_time": 1710000300,
                    "mapping": {
                        "node-system": {
                            "id": "node-system",
                            "message": None,
                            "parent": None,
                            "children": ["node-user"],
                        },
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
                            "parent": "node-system",
                            "children": ["node-assistant"],
                        },
                        "node-assistant": {
                            "id": "node-assistant",
                            "message": {
                                "id": "msg-assistant",
                                "author": {"role": "assistant"},
                                "create_time": 1710000005,
                                "content": {
                                    "content_type": "text",
                                    "parts": [
                                        "Start with Shinjuku.",
                                        " Then visit Asakusa.",
                                    ],
                                },
                                "metadata": {"model_slug": "gpt-4o-mini"},
                            },
                            "parent": "node-user",
                            "children": [],
                        },
                    },
                }
            ]
        )
    )

    conversations = list(ChatGPTExportConnector(export_path).fetch())

    assert len(conversations) == 1
    conversation = conversations[0]
    assert conversation.id == "chatgpt-conv-1"
    assert conversation.source == "chatgpt"
    assert conversation.title == "Tokyo ideas"
    assert conversation.created_at == datetime(2024, 3, 9, 16, 0, 0, tzinfo=timezone.utc)
    assert [participant.role for participant in conversation.participants] == ["user", "assistant"]
    assert [message.id for message in conversation.messages_in_chronological_order()] == [
        "msg-user",
        "msg-assistant",
    ]
    assert conversation.messages_in_chronological_order()[1].text_content == (
        "Start with Shinjuku. Then visit Asakusa."
    )


def test_claude_export_connector_parses_embedded_messages_json(tmp_path) -> None:
    export_path = tmp_path / "claude-export.json"
    export_path.write_text(
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

    conversations = list(ClaudeExportConnector(export_path).fetch())

    assert len(conversations) == 1
    conversation = conversations[0]
    assert conversation.id == "claude-conv-1"
    assert conversation.source == "claude"
    assert conversation.title == "Release summary"
    assert [participant.role for participant in conversation.participants] == ["user", "assistant"]
    assert [message.id for message in conversation.messages_in_chronological_order()] == [
        "claude-msg-1",
        "claude-msg-2",
    ]
    assert conversation.messages_in_chronological_order()[0].participant.role == "user"
    assert conversation.messages_in_chronological_order()[1].text_content == (
        "Here is the summary. It covers three changes."
    )


def test_codex_local_state_connector_parses_single_session_file(tmp_path) -> None:
    session_path = tmp_path / "session.jsonl"
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
                            "cwd": "/workspace/taildrop",
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

    conversations = list(CodexLocalStateConnector(session_path).fetch())

    assert len(conversations) == 1
    conversation = conversations[0]
    assert conversation.id == "session-1"
    assert conversation.source == "codex"
    assert conversation.title == "Check Taildrop config."
    assert conversation.created_at == datetime(2026, 3, 16, 2, 15, 14, 189000, tzinfo=timezone.utc)
    assert conversation.updated_at == datetime(2026, 3, 16, 2, 16, 24, 332000, tzinfo=timezone.utc)
    assert conversation.metadata == {
        "codex": {
            "cwd": "/workspace/taildrop",
            "cli_version": "0.114.0",
            "model_provider": "openai",
            "session_source": "cli",
            "session_file": str(session_path),
        }
    }
    assert [participant.role for participant in conversation.participants] == ["user", "assistant"]
    assert [message.role for message in conversation.messages_in_chronological_order()] == ["user", "assistant"]
    assert [message.text_content for message in conversation.messages_in_chronological_order()] == [
        "Check Taildrop config.",
        "Taildrop is enabled.",
    ]


def test_codex_local_state_connector_scans_codex_root_directory(tmp_path) -> None:
    sessions_dir = tmp_path / ".codex" / "sessions" / "2026" / "03" / "16"
    sessions_dir.mkdir(parents=True)

    first_session = sessions_dir / "rollout-a.jsonl"
    first_session.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-03-16T01:00:00Z",
                        "type": "session_meta",
                        "payload": {"id": "session-a", "timestamp": "2026-03-16T01:00:00Z"},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-03-16T01:00:01Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "First session"}],
                        },
                    }
                ),
            ]
        )
        + "\n"
    )

    second_session = sessions_dir / "rollout-b.jsonl"
    second_session.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-03-16T02:00:00Z",
                        "type": "session_meta",
                        "payload": {"id": "session-b", "timestamp": "2026-03-16T02:00:00Z"},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-03-16T02:00:02Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [{"type": "output_text", "text": "Second session"}],
                        },
                    }
                ),
            ]
        )
        + "\n"
    )

    conversations = list(CodexLocalStateConnector(tmp_path / ".codex").fetch())

    assert [conversation.id for conversation in conversations] == ["session-a", "session-b"]
    assert [conversation.messages_in_chronological_order()[0].text_content for conversation in conversations] == [
        "First session",
        "Second session",
    ]
