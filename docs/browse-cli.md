# Browse CLI

`conversation-hub browse` opens a local interactive terminal browser over normalized conversations. It supports both direct mode with `--input` and a no-required-args workflow that can import from a provider and then browse immediately. The flow stays in the terminal, uses stdlib input/output, and keeps all data local and human-readable.

## Command

```bash
conversation-hub browse
conversation-hub browse --input INPUT_PATH
```

## Arguments

- `--input`: optional path to a normalized JSON conversation file

If `--input` is omitted, the workflow prompts you to:

- open an existing normalized JSON file
- import from `chatgpt`, `claude`, or `codex`
- enter the source path interactively
- enter the normalized output path interactively

If you leave the output path blank during provider import, the workflow writes to `./.conversation-hub/normalized/<provider>.json`.

## Example

```bash
conversation-hub browse
conversation-hub browse --input ./normalized/conversations.json
```

The session is prompt-driven. In the main list:

- type a conversation number to open it
- type `r` to print an overall report for the current conversation view
- type `f` to filter the conversation list by keyword in titles, sources, participants, tags, and message text
- type `q` to quit

Inside a selected conversation:

- type `m` to print the conversation messages
- type `a` to run one-off analysis for just that conversation
- type `b` to go back to the conversation list
- type `q` to quit

## Example flow

```text
$ conversation-hub browse
Choose how to load conversations
================================
1. Open an existing normalized JSON file
2. Import from a provider and browse it now
q. Quit
Workflow command [1, 2, q]:
2
Choose provider [chatgpt, claude, codex]:
codex
Enter the source path for codex:
/home/sindri/.codex
Enter normalized output path [default: /home/sindri/conversation-hub/.conversation-hub/normalized/codex.json]:

Imported 2 conversations (14 messages) from codex to /home/sindri/conversation-hub/.conversation-hub/normalized/codex.json
Opening browser for 2 conversations from normalized JSON.
Conversation browser
====================
1. Taildrop release checklist | source=codex | messages=2 | updated=2024-03-09T16:00:05+00:00
2. Ops sync | source=codex | messages=2 | updated=2024-03-10T09:05:00+00:00
List command [number, r, f, q]:
f
Enter filter keyword [blank clears]:
ops
Showing 1 conversation matching 'ops'.
Conversation browser
====================
Active filter: ops
1. Ops sync | source=codex | messages=2 | updated=2024-03-10T09:05:00+00:00
List command [number, r, f, q]:
1
Conversation 1
================
ID: conv-2
Title: Ops sync
Source: codex
Messages: 2
Participants: user, assistant
Created: 2024-03-10T09:00:00+00:00
Updated: 2024-03-10T09:05:00+00:00
Tags: (none)
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

- The CLI stays thin by dispatching to reusable interactive modules: `conversation_hub.interactive.run_browse_workflow()` for the no-args setup flow and `conversation_hub.interactive.run_browse_session()` for the visible browser session.
- The terminal report reuses the shared `conversation_hub.pipelines.run_analysis()` heuristics for both the overall report and one-conversation analysis.
- The current MVP is local and human-readable by design. It does not depend on SQLite, embeddings, or network calls.
