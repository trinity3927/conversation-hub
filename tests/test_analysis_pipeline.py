from __future__ import annotations

import json

import conversation_hub.storage as storage
from conversation_hub.pipelines import run_analysis


def test_run_analysis_reports_default_heuristic_sections(tmp_path) -> None:
    payload = [
        {
            "id": "chatgpt-1",
            "source": "chatgpt",
            "title": "Taildrop release checklist",
            "participants": [
                {"id": "user", "role": "user", "display_name": None, "metadata": {}},
                {"id": "assistant", "role": "assistant", "display_name": None, "metadata": {}},
            ],
            "messages": [
                {
                    "id": "chatgpt-1-msg-1",
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
                    "id": "chatgpt-1-msg-2",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Here is a deterministic Taildrop release checklist.",
                            "metadata": {},
                        }
                    ],
                    "created_at": "2024-03-09T16:00:05+00:00",
                    "metadata": {},
                },
                {
                    "id": "chatgpt-1-msg-3",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Use bullet points.", "metadata": {}}],
                    "created_at": "2024-03-09T16:00:07+00:00",
                    "metadata": {},
                },
                {
                    "id": "chatgpt-1-msg-4",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [{"kind": "text", "text": "Bullet points added.", "metadata": {}}],
                    "created_at": "2024-03-09T16:00:09+00:00",
                    "metadata": {},
                },
            ],
            "created_at": "2024-03-09T16:00:00+00:00",
            "updated_at": "2024-03-09T16:00:09+00:00",
            "tags": [],
            "metadata": {},
        },
        {
            "id": "codex-1",
            "source": "codex",
            "title": "Taildrop rollback planning",
            "participants": [
                {"id": "user", "role": "user", "display_name": None, "metadata": {}},
                {"id": "assistant", "role": "assistant", "display_name": None, "metadata": {}},
            ],
            "messages": [
                {
                    "id": "codex-1-msg-1",
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
                    "created_at": "2024-03-10T16:00:01+00:00",
                    "metadata": {},
                },
                {
                    "id": "codex-1-msg-2",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Drafted the Taildrop release checklist with bullets.",
                            "metadata": {},
                        }
                    ],
                    "created_at": "2024-03-10T16:00:05+00:00",
                    "metadata": {},
                },
                {
                    "id": "codex-1-msg-3",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Can you also audit the rollback plan for Taildrop?",
                            "metadata": {},
                        }
                    ],
                    "created_at": "2024-03-10T16:00:10+00:00",
                    "metadata": {},
                },
            ],
            "created_at": "2024-03-10T16:00:00+00:00",
            "updated_at": "2024-03-10T16:00:10+00:00",
            "tags": [],
            "metadata": {},
        },
        {
            "id": "chatgpt-2",
            "source": "chatgpt",
            "title": "Codex CLI notes",
            "participants": [
                {"id": "user", "role": "user", "display_name": None, "metadata": {}},
                {"id": "assistant", "role": "assistant", "display_name": None, "metadata": {}},
            ],
            "messages": [
                {
                    "id": "chatgpt-2-msg-1",
                    "participant": {
                        "id": "user",
                        "role": "user",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Summarize Codex CLI steps for the Taildrop repo. Use bullet points.",
                            "metadata": {},
                        }
                    ],
                    "created_at": "2024-03-11T16:00:01+00:00",
                    "metadata": {},
                },
                {
                    "id": "chatgpt-2-msg-2",
                    "participant": {
                        "id": "assistant",
                        "role": "assistant",
                        "display_name": None,
                        "metadata": {},
                    },
                    "parts": [
                        {
                            "kind": "text",
                            "text": "Codex CLI can inspect the Taildrop repo quickly.",
                            "metadata": {},
                        }
                    ],
                    "created_at": "2024-03-11T16:00:05+00:00",
                    "metadata": {},
                },
            ],
            "created_at": "2024-03-11T16:00:00+00:00",
            "updated_at": "2024-03-11T16:00:05+00:00",
            "tags": [],
            "metadata": {},
        },
    ]
    input_path = tmp_path / "normalized.json"
    input_path.write_text(json.dumps(payload), encoding="utf-8")

    report = run_analysis(storage.load_conversations_json(input_path)).to_dict()

    assert report["summary"] == {
        "conversation_count": 3,
        "message_count": 9,
        "source_counts": {"chatgpt": 2, "codex": 1},
    }
    assert [pattern["source"] for pattern in report["source_patterns"]] == ["chatgpt", "codex"]
    assert "taildrop" in report["source_patterns"][0]["top_keywords"]
    assert report["recurring_projects_goals"] == [
        {
            "count": 3,
            "phrase": "taildrop release checklist",
            "sources": ["chatgpt", "codex"],
        }
    ]
    assert report["important_entities"][:2] == [
        {"count": 7, "entity": "Taildrop", "kind": "name", "sources": ["chatgpt", "codex"]},
        {"count": 2, "entity": "Codex CLI", "kind": "name", "sources": ["chatgpt"]},
    ]
    assert report["reusable_prompts"] == [
        {
            "count": 2,
            "prompt": "Draft a Taildrop release checklist. Keep it deterministic.",
            "sources": ["chatgpt", "codex"],
        }
    ]
    assert report["repeated_preferences_constraints"] == [
        {
            "count": 2,
            "sources": ["chatgpt", "codex"],
            "text": "Keep it deterministic.",
        },
        {
            "count": 2,
            "sources": ["chatgpt"],
            "text": "Use bullet points.",
        },
    ]
    assert report["unresolved_threads"] == [
        {
            "conversation_id": "codex-1",
            "last_message_id": "codex-1-msg-3",
            "reason": "last_message_from_user",
            "source": "codex",
            "title": "Taildrop rollback planning",
            "excerpt": "Can you also audit the rollback plan for Taildrop?",
        }
    ]
