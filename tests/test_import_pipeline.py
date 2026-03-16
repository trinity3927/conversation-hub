from __future__ import annotations

import json

from conversation_hub.models.schema import Conversation
from conversation_hub.pipelines.import_pipeline import run_import


def test_run_import_returns_conversations_and_counts_for_chatgpt(tmp_path) -> None:
    input_path = tmp_path / "conversations.json"
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
                            },
                        },
                    },
                }
            ]
        )
    )

    result = run_import("chatgpt", input_path)

    assert result.source == "chatgpt"
    assert result.input_path == input_path
    assert result.conversation_count == 1
    assert result.message_count == 2
    assert len(result.conversations) == 1
    assert isinstance(result.conversations[0], Conversation)
    assert result.conversations[0].id == "chatgpt-conv-1"


def test_run_import_supports_codex_directory_inputs(tmp_path) -> None:
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

    result = run_import("codex", codex_root)

    assert result.source == "codex"
    assert result.input_path == codex_root
    assert result.conversation_count == 1
    assert result.message_count == 2
    assert [conversation.id for conversation in result.conversations] == ["session-1"]
