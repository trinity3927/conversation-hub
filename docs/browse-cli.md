# Browse CLI

`conversation-hub browse` opens a local interactive terminal browser over conversations. It supports both direct mode with `--input` and a no-required-args workflow that can reopen recent datasets, import from a provider, open normalized JSON, or open a local SQLite export and then browse immediately. The flow stays in the terminal, uses stdlib input/output, and keeps all data local and human-readable.

## Command

```bash
conversation-hub browse
conversation-hub browse --input INPUT_PATH
```

## Arguments

- `--input`: optional path to a normalized JSON conversation file

If `--input` is omitted, the workflow opens a minimal home screen with:

- recent datasets you can reopen by number
- remembered defaults such as the last browse filter and provider import paths
- quick actions to import from `chatgpt`, `claude`, or `codex`
- quick actions to open normalized JSON or SQLite directly

The launcher stores that local state in `./.conversation-hub/state.json`. If you leave the output path blank during provider import, the workflow writes normalized JSON to `./.conversation-hub/normalized/<provider>.json`.

## Example

```bash
conversation-hub browse
conversation-hub browse --input ./normalized/conversations.json
```

## Browser controls

The browser is prompt-driven and prints the visible controls each time you enter a view.

In the browse list:

- type a conversation number to open it
- type `n` or `p` to move between pages
- type `f` to filter the current conversation list by keyword in titles, sources, participants, tags, and message text
- type `/` to set a non-destructive search query for the current filtered view
- type `r` to print an overall report for the current view
- type `q` to quit

Inside a selected conversation:

- type `m` to print the conversation messages
- type `a` to run one-off analysis for just that conversation
- type `t` to print tags and metadata/provenance
- type `b` to go back to the conversation list
- type `q` to quit

The main list shows paged conversation cards with:

- title
- source, message count, and updated timestamp
- short preview text
- likely tasks inferred from user asks
- extracted artifacts such as file paths and URLs

The in-terminal report stays focused on high-signal sections:

- `Quick summary`
- `Repeated constraints/preferences`
- `Likely tasks`
- `Unresolved asks`
- `Artifacts`
- `Source comparison`

## Example flow

```text
$ conversation-hub browse
Conversation Hub
================
Minimal home

Recent datasets
---------------
(none)

Remembered defaults
-------------------
Last browse filter: (none)
Provider paths: (none)

Quick actions
-------------
i import provider export
j open normalized JSON
s open local SQLite export
q quit
Home command [recent number, i, j, s, q]:
i
Choose provider [chatgpt, claude, codex]:
codex
Enter source path for codex [default: ~/.codex]:

Enter normalized output path [default: ./.conversation-hub/normalized/codex.json]:

Imported 2 conversations (14 messages) from codex to ./.conversation-hub/normalized/codex.json
Opening browser for 2 conversations from normalized JSON.
Conversation Browser
====================
Mode: browse list
Dataset summary: 2 conversations | 14 messages | codex=2

View: showing 1-2 of 2 | page 1/1

1. Taildrop release checklist
   codex | 8 msgs | updated 2024-03-09T16:00:05+00:00
   preview: Draft the Taildrop release checklist.
   tasks: draft release checklist
2. Ops sync
   codex | 6 msgs | updated 2024-03-10T09:05:00+00:00
   preview: Check Taildrop access in staging.
   tasks: check access staging

Legend: [number open] [n next] [p prev] [f filter] [/ search] [r report] [q quit]
List command [number, n, p, f, /, r, q]:
```

## Notes

- The CLI stays thin by dispatching to reusable interactive modules: `conversation_hub.interactive.run_browse_workflow()` for the no-args setup flow and `conversation_hub.interactive.run_browse_session()` for the visible browser session.
- Opening a SQLite export in the launcher rehydrates conversations through `conversation_hub.storage.load_conversations_sqlite()`, then enters the same browse session used for normalized JSON.
- The terminal report reuses the shared `conversation_hub.pipelines.run_analysis()` heuristics for counts, source comparison, repeated constraints, and unresolved asks, then adds browse-specific task and artifact summaries.
- The browse workflow is local, human-readable, stdlib-only, and testable with injected input/output functions.
