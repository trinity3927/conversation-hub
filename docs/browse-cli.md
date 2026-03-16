# Browse CLI

`conversation-hub browse` loads normalized conversation JSON and opens a local interactive terminal browser. The first version is intentionally simple: it stays in the terminal, uses stdlib input/output, and prints a readable report instead of writing extra files.

## Command

```bash
conversation-hub browse --input INPUT_PATH
```

## Arguments

- `--input`: required path to a normalized JSON conversation file

## Example

```bash
conversation-hub browse --input ./normalized/conversations.json
```

The session is prompt-driven. In the main list:

- type a conversation number to open it
- type `r` to print an overall report for all loaded conversations
- type `q` to quit

Inside a selected conversation:

- type `m` to print the conversation messages
- type `a` to run one-off analysis for just that conversation
- type `b` to go back to the conversation list
- type `q` to quit

## Example flow

```text
$ conversation-hub browse --input ./normalized/conversations.json
Conversation browser
====================
1. Taildrop release checklist | source=chatgpt | messages=2 | updated=2024-03-09T16:00:05+00:00
2. Ops sync | source=codex | messages=2 | updated=2024-03-10T09:05:00+00:00
List command [number, r, q]:
2
Conversation 2
================
ID: conv-2
Title: Ops sync
Source: codex
Messages: 2
Conversation command [m, a, b, q]:
m
Messages for conv-2
====================
1. [user] Check Taildrop access in staging.
2. [assistant] Taildrop staging access is ready.
Conversation command [m, a, b, q]:
a
Analysis report for conversation conv-2
=======================================
Conversations: 1
Messages: 2
Source counts: codex=1
```

## Notes

- The CLI stays thin by reloading normalized JSON with `conversation_hub.storage.load_conversations_json()` and dispatching to `conversation_hub.interactive.run_browse_session()`.
- The terminal report reuses the shared `conversation_hub.pipelines.run_analysis()` heuristics for both the overall report and one-conversation analysis.
- The current MVP is local and human-readable by design. It does not depend on SQLite, embeddings, or network calls.
