# conversation-hub

A Python project for pulling AI conversations from multiple sources, normalizing them into a common schema, organizing them for search/review, and running configurable actions on top of them.

## Setup

1. Use Python 3.11 or newer.
2. Create and activate a virtual environment.
3. Install the project in editable mode:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Development note: in this workspace, `pytest` is available from `/home/sindri/.hermes/hermes-agent/venv/bin/python`, so test runs should use `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest ...`.

## Supported sources

- `chatgpt`: ChatGPT export files shaped like `conversations.json`
- `claude`: Claude JSON exports containing `conversations` and embedded `messages` or `chat_messages`

## Import CLI

The CLI imports one local export file, runs it through the selected connector, and writes normalized JSON.

```bash
conversation-hub import --source chatgpt --input ./exports/conversations.json --output ./normalized/chatgpt.json
conversation-hub import --source claude --input ./exports/claude.json --output ./normalized/claude.json
```

Each successful run prints a concise summary such as:

```text
Imported 1 conversation (2 messages) from chatgpt to normalized/chatgpt.json
```

See [docs/import-cli.md](docs/import-cli.md) for the full command reference and [docs/import-architecture.md](docs/import-architecture.md) for the import flow.

## Normalized output

The import command writes a UTF-8 JSON array of normalized conversations.

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
