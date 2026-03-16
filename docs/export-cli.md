# Export CLI

`conversation-hub export` reads normalized conversation JSON, reconstructs shared `Conversation` objects, and writes them into a deterministic local SQLite database.

## Command

```bash
conversation-hub export --format sqlite --input INPUT_PATH --output OUTPUT_PATH
```

## Arguments

- `--format`: required export target; the first supported value is `sqlite`
- `--input`: required path to a normalized JSON conversation file
- `--output`: required path for the SQLite database file that will be written

Unsupported `--format` values are rejected by `argparse` with exit code `2`.

## Example

```bash
conversation-hub export \
  --format sqlite \
  --input ./normalized/conversations.json \
  --output ./storage/conversations.db
```

Successful runs print a short summary:

```text
Exported 12 conversations (248 messages) from ./normalized/conversations.json to ./storage/conversations.db as sqlite
```

The command stays intentionally thin:
- `argparse` validates `--format`, `--input`, and `--output`
- `conversation_hub.storage.load_conversations_json()` reloads normalized conversations into shared dataclasses
- `conversation_hub.storage.write_conversations_sqlite()` creates the schema, rewrites managed rows for the input conversations, and returns summary counts

## SQLite table layout

- `conversations`: one row per normalized conversation keyed by `(source, id)` with title, timestamps, tags, and metadata
- `participants`: one row per conversation-scoped participant keyed by `(conversation_source, conversation_id, participant_key)` with stable `sort_index`
- `messages`: one row per normalized message keyed by `(conversation_source, conversation_id, id)` with chronological `sort_index`, participant linkage, timestamps, and metadata
- `content_parts`: one row per message part keyed by `(conversation_source, conversation_id, message_id, part_index)` with `kind`, `text`, and metadata

## Determinism notes

- Timestamps are stored as ISO-8601 strings with explicit UTC offsets.
- `messages.sort_index` follows the normalized chronological ordering from the shared schema helpers.
- JSON payload columns such as `tags_json` and `metadata_json` use canonical JSON encoding with sorted keys.
- Re-exporting the same conversation set replaces the managed rows for those `(source, id)` keys instead of duplicating them.
