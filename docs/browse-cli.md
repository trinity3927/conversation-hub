# Browse CLI

`conversation-hub browse` opens a local interactive terminal browser over conversations. It supports both direct mode with `--input` and a no-required-args workflow that can open normalized JSON, import from a provider, or open a local SQLite export and then browse immediately. The flow stays in the terminal, uses stdlib input/output, and keeps all data local and human-readable.

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
- open an existing SQLite export
- enter the source path interactively
- enter the normalized output path interactively

If you leave the output path blank during provider import, the workflow writes to `./.conversation-hub/normalized/<provider>.json`.

## Example

```bash
conversation-hub browse
conversation-hub browse --input ./normalized/conversations.json
```

The session is prompt-driven and prints visible command help each time you enter a view.

In the main list:

- type a conversation number to open it
- type `r` to print an overall report for the current conversation view
- type `f` to filter the conversation list by keyword in titles, sources, participants, tags, and message text
- type `q` to quit

Inside a selected conversation:

- type `m` to print the conversation messages
- type `a` to run one-off analysis for just that conversation
- type `t` to print tags and metadata/provenance
- type `b` to go back to the conversation list
- type `q` to quit

The main list now shows richer previews for each conversation, including title, source, message count, last-updated timestamp, and a short excerpt. The interactive report still uses the shared analysis pipeline, but the terminal renderer omits low-value raw `top_keywords` output so the report stays easier to scan.

## Example flow

```text
$ conversation-hub browse
Browse launcher
===============
1. Open an existing normalized JSON file
2. Import from a provider and browse it now
3. Open a local SQLite export
q. Quit
Workflow command [1, 2, 3, q]:
2
Choose provider [chatgpt, claude, codex]:
codex
Enter the source path for codex:
/home/sindri/.codex
Enter normalized output path [default: /home/sindri/conversation-hub/.conversation-hub/normalized/codex.json]:

Imported 2 conversations (14 messages) from codex to /home/sindri/conversation-hub/.conversation-hub/normalized/codex.json
Opening browser for 2 conversations from normalized JSON.
Conversation Browser
====================
Loaded conversations: 2

Conversation list
-----------------
1. Taildrop release checklist
   source: codex | messages: 2 | updated: 2024-03-09T16:00:05+00:00
   preview: Draft the Taildrop release checklist.
2. Ops sync
   source: codex | messages: 2 | updated: 2024-03-10T09:05:00+00:00
   preview: Check Taildrop access in staging.

Main commands
-------------
[number] open conversation
r overall report for current view
f filter conversations by keyword
q quit browser
List command [number, r, f, q]:
f
Enter filter keyword [blank clears]:
ops
Showing 1 conversation matching 'ops'.
Conversation Browser
====================
Loaded conversations: 1
Active filter: ops

Conversation list
-----------------
1. Ops sync
   source: codex | messages: 2 | updated: 2024-03-10T09:05:00+00:00
   preview: Check Taildrop access in staging.

Main commands
-------------
[number] open conversation
r overall report for current view
f filter conversations by keyword
q quit browser
List command [number, r, f, q]:
1
Conversation 1 of 1
===================
ID: conv-2
Title: Ops sync
Source: codex
Messages: 2
Participants: user, assistant
Created: 2024-03-10T09:00:00+00:00
Updated: 2024-03-10T09:05:00+00:00
Tags: (none)
Preview: Check Taildrop access in staging.

Conversation commands
---------------------
m show messages
a analysis report
t metadata and tags
b back to conversation list
q quit browser
Conversation command [m, a, t, b, q]:
t

Conversation metadata
---------------------
Tags: (none)
Metadata: (none)
Conversation command [m, a, t, b, q]:
a
Analysis report for conversation conv-2
=======================================
Conversations: 1
Messages: 2
Source counts: codex=1
```

## Notes

- The CLI stays thin by dispatching to reusable interactive modules: `conversation_hub.interactive.run_browse_workflow()` for the no-args setup flow and `conversation_hub.interactive.run_browse_session()` for the visible browser session.
- Opening a SQLite export in the launcher rehydrates conversations through `conversation_hub.storage.load_conversations_sqlite()`, then enters the same browse session used for normalized JSON.
- The terminal report reuses the shared `conversation_hub.pipelines.run_analysis()` heuristics for both the overall report and one-conversation analysis.
- The browse workflow is local, human-readable, stdlib-only, and testable with injected input/output functions.
