# Search CLI

`conversation-hub search` queries a local SQLite export created by `conversation-hub export --format sqlite` and writes deterministic JSON results to stdout.

## Command

```bash
conversation-hub search --input PATH --query QUERY [--limit N]
```

Arguments:

- `--input`: path to the SQLite database file to search
- `--query`: case-insensitive text to match in conversation titles and text content parts
- `--limit`: optional maximum number of results to return; defaults to `10`

## Example

```bash
conversation-hub export --format sqlite --input ./normalized/conversations.json --output ./storage/conversations.db
conversation-hub search --input ./storage/conversations.db --query Taildrop --limit 3
```

Example output:

```json
{
  "limit": 3,
  "query": "Taildrop",
  "result_count": 2,
  "results": [
    {
      "conversation_id": "conv-2",
      "excerpt": "Taildrop release checklist",
      "message_count": 4,
      "source": "chatgpt",
      "title": "Taildrop release checklist"
    },
    {
      "conversation_id": "session-1",
      "excerpt": "Check Taildrop access in staging.",
      "message_count": 2,
      "source": "codex",
      "title": "Ops sync"
    }
  ]
}
```

## Search behavior

- Searches conversation titles and `content_parts.text`
- Uses case-insensitive substring matching
- Returns deterministic JSON with sorted keys
- Orders matches by title hits first, then newer conversations, then stable source/id tie-breakers
