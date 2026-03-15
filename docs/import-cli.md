# Import CLI

`conversation-hub import` reads one supported export file, normalizes it through the selected connector, and writes normalized JSON output.

## Command

```bash
conversation-hub import --source SOURCE --input INPUT_PATH --output OUTPUT_PATH
```

## Arguments

- `--source`: required source selector; supported values are `chatgpt` and `claude`
- `--input`: required path to the source export file
- `--output`: required path for the normalized JSON file that will be written

Unsupported `--source` values are rejected by `argparse` with exit code `2`.

## Examples

ChatGPT export:

```bash
conversation-hub import \
  --source chatgpt \
  --input ./exports/conversations.json \
  --output ./normalized/chatgpt.json
```

Claude export:

```bash
conversation-hub import \
  --source claude \
  --input ./exports/claude-export.json \
  --output ./normalized/claude.json
```

Successful runs print a short summary:

```text
Imported 12 conversations (248 messages) from chatgpt to ./normalized/chatgpt.json
```

## Output structure

The command writes a JSON array. Each item is one normalized conversation with this shape:

```json
{
  "id": "conv-1",
  "source": "chatgpt",
  "title": "Trip ideas",
  "participants": [
    {
      "id": "user",
      "role": "user",
      "display_name": null,
      "metadata": {}
    }
  ],
  "messages": [
    {
      "id": "msg-1",
      "participant": {
        "id": "user",
        "role": "user",
        "display_name": null,
        "metadata": {}
      },
      "parts": [
        {
          "kind": "text",
          "text": "Plan me a trip to Tokyo.",
          "metadata": {}
        }
      ],
      "created_at": "2024-03-09T16:00:01+00:00",
      "metadata": {}
    }
  ],
  "created_at": "2024-03-09T16:00:00+00:00",
  "updated_at": "2024-03-09T16:05:00+00:00",
  "tags": [],
  "metadata": {}
}
```

## Output notes

- Timestamps are emitted as ISO-8601 strings.
- `messages` are written in chronological order, even if the source export stored them differently.
- `parts` preserve structured content so non-text items can keep metadata without being flattened into plain text.
- `metadata` fields are passed through as JSON-compatible dictionaries for downstream processing.
