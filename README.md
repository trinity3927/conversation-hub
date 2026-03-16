# conversation-hub

A Python project for pulling AI conversations from multiple sources, normalizing them into a common schema, exporting them into local storage, organizing them for search/review, and running configurable actions on top of them.

## Setup

1. Use Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For local development and tests, install the dev extras:

```bash
pip install -e ".[dev]"
```

Run tests with:

```bash
PYTHONPATH=src python -m pytest
```

## Supported sources

- `chatgpt`: ChatGPT export files shaped like `conversations.json`
- `claude`: Claude JSON exports containing `conversations` and embedded `messages` or `chat_messages`
- `codex`: Codex CLI local state from a single session `*.jsonl` file or a `.codex/sessions/**/*.jsonl` directory tree

## Import CLI

The CLI imports one local export file or local state directory by parsing arguments, calling the shared import pipeline, and writing normalized JSON.

```bash
conversation-hub import --source chatgpt --input ./exports/conversations.json --output ./normalized/chatgpt.json
conversation-hub import --source claude --input ./exports/claude.json --output ./normalized/claude.json
conversation-hub import --source codex --input ~/.codex --output ./normalized/codex.json
```

Each successful run prints a concise summary such as:

```text
Imported 1 conversation (2 messages) from chatgpt to normalized/chatgpt.json
```

For Codex imports, normalized conversation metadata preserves useful local provenance under `metadata.codex`, including `cwd`, `cli_version`, `model_provider`, `session_source`, and `session_file`.

Internally, source registration now lives in a shared connector registry and import execution lives in `conversation_hub.pipelines.run_import()`, so both the CLI and future workflows can reuse the same source resolution and summary-count logic.

See [docs/import-cli.md](docs/import-cli.md) for the full command reference and [docs/import-architecture.md](docs/import-architecture.md) for the import flow.

## Analyze CLI

The CLI can also analyze normalized JSON conversations and write a deterministic JSON report with simple local heuristics.

```bash
conversation-hub analyze --input ./normalized/conversations.json --output ./reports/analysis.json
```

Each successful run prints a concise summary such as:

```text
Analyzed 3 conversations (9 messages) from ./normalized/conversations.json to ./reports/analysis.json
```

Internally, the command loads normalized JSON back into `Conversation` objects with `conversation_hub.storage.load_conversations_json()` and runs the reusable analysis pipeline through `conversation_hub.pipelines.run_analysis()`.

See [docs/analyze-cli.md](docs/analyze-cli.md) for the report shape and heuristic details.

## Browse CLI

The CLI can browse local conversations in a prompt-driven terminal session. It supports both direct mode for normalized JSON and a no-required-args workflow that can open recent datasets, import from `chatgpt`, `claude`, or `codex`, open normalized JSON, or open a local SQLite export before dropping into the same browser.

```bash
conversation-hub browse
conversation-hub browse --input ./normalized/conversations.json
```

If you choose provider import in the no-args flow, the workflow prompts for the source path and normalized output path. Leaving the output path blank writes a human-readable JSON file under `./.conversation-hub/normalized/<provider>.json`. The launcher also keeps a local JSON state file under `./.conversation-hub/state.json` so it can remember recent datasets and the last provider paths you used.

The no-args home screen shows:

- recent datasets you can reopen by number
- remembered defaults such as the last browse filter and provider import paths
- quick actions for provider import, normalized JSON, and SQLite

Main list commands:

- type a conversation number to open it
- type `n` or `p` to move between pages
- type `r` to print an overall report for the current view
- type `f` to filter the current conversation list by keyword
- type `/` to set a non-destructive search query for the current filtered view
- type `q` to quit

Selected conversation commands:

- type `m` to print messages
- type `a` to analyze just that conversation
- type `t` to show tags and metadata/provenance
- type `b` to go back
- type `q` to quit

The browser prints visible command help in both the conversation list and selected conversation views, uses paged conversation cards with previews/tasks/artifacts, and keeps the in-terminal report focused on higher-signal sections such as quick summary, likely tasks, unresolved asks, artifacts, and source comparison instead of noisy raw keyword dumps.

Internally, `conversation-hub browse --input ...` reloads normalized JSON with `conversation_hub.storage.load_conversations_json()` and hands the conversations to the reusable interactive session in `conversation_hub.interactive.run_browse_session()`. Running `conversation-hub browse` without `--input` dispatches into `conversation_hub.interactive.run_browse_workflow()`, which handles interactive loading/import before opening the same browser session. The SQLite branch rehydrates conversations through `conversation_hub.storage.load_conversations_sqlite()`.

See [docs/browse-cli.md](docs/browse-cli.md) for the interaction flow and a full example.

## Export CLI

The CLI can export normalized JSON conversations into a deterministic local SQLite database.

```bash
conversation-hub export --format sqlite --input ./normalized/conversations.json --output ./storage/conversations.db
```

Each successful run prints a concise summary such as:

```text
Exported 3 conversations (9 messages) from ./normalized/conversations.json to ./storage/conversations.db as sqlite
```

Internally, the command reloads normalized JSON with `conversation_hub.storage.load_conversations_json()` and dispatches to the reusable SQLite writer through `conversation_hub.storage.write_conversations_sqlite()`.

See [docs/export-cli.md](docs/export-cli.md) for the command reference and SQLite table layout.

## Search CLI

The CLI can search a local SQLite export and print deterministic JSON results to stdout.

```bash
conversation-hub search --input ./storage/conversations.db --query Taildrop
conversation-hub search --input ./storage/conversations.db --query Taildrop --limit 5
```

Typical local workflow:

```bash
conversation-hub export --format sqlite --input ./normalized/conversations.json --output ./storage/conversations.db
conversation-hub search --input ./storage/conversations.db --query Taildrop --limit 3
```

The first search pass matches conversation titles and text content parts, then orders results deterministically so repeated runs are easy to diff and script against.

See [docs/search-cli.md](docs/search-cli.md) for the command reference and JSON result shape.

## Normalized output

The import command writes a UTF-8 JSON array of normalized conversations. That same normalized JSON is the input format for `conversation-hub analyze`, `conversation-hub browse`, and `conversation-hub export --format sqlite`.

- Timestamps are serialized as ISO-8601 strings with explicit UTC offsets such as `2024-03-09T16:00:00+00:00`.
- Conversations include stable top-level keys for `id`, `source`, `title`, `participants`, `messages`, `created_at`, `updated_at`, `tags`, and `metadata`.
- Messages are serialized in chronological order to make the output easier to diff and consume downstream.
- Content is preserved as structured `parts`, so text and non-text payloads can stay distinct.

Example normalized shape:

```json
[
  {
    "id": "conv-1",
    "source": "chatgpt",
    "title": "Example",
    "participants": [],
    "messages": [],
    "created_at": "2024-03-09T16:00:00+00:00",
    "updated_at": "2024-03-09T16:05:00+00:00",
    "tags": [],
    "metadata": {}
  }
]
```

## Default analysis output

The first analysis MVP emits a deterministic JSON object with these top-level sections:

- `summary`
- `source_patterns`
- `recurring_projects_goals`
- `important_entities`
- `reusable_prompts`
- `repeated_preferences_constraints`
- `unresolved_threads`
