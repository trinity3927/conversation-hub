# Analyze CLI

`conversation-hub analyze` reads normalized conversation JSON, reconstructs shared `Conversation` objects, runs the reusable analysis pipeline, and writes a deterministic JSON report.

## Command

```bash
conversation-hub analyze --input INPUT_PATH --output OUTPUT_PATH
```

## Arguments

- `--input`: required path to a normalized JSON conversation file
- `--output`: required path for the analysis JSON report that will be written

## Example

```bash
conversation-hub analyze \
  --input ./normalized/conversations.json \
  --output ./reports/analysis.json
```

Successful runs print a short summary:

```text
Analyzed 12 conversations (248 messages) from ./normalized/conversations.json to ./reports/analysis.json
```

## Report structure

The command writes one JSON object with stable top-level sections:

```json
{
  "summary": {
    "conversation_count": 12,
    "message_count": 248,
    "source_counts": {
      "chatgpt": 8,
      "codex": 4
    }
  },
  "source_patterns": [],
  "recurring_projects_goals": [],
  "important_entities": [],
  "reusable_prompts": [],
  "repeated_preferences_constraints": [],
  "unresolved_threads": []
}
```

## Heuristic notes

- `summary`: total conversation/message counts plus conversation counts per source
- `source_patterns`: per-source counts plus top keyword hints from titles and user messages
- `recurring_projects_goals`: repeated leading project-style phrases extracted from titles and user requests
- `important_entities`: repeated capitalized names found in message text
- `reusable_prompts`: repeated full user prompts
- `repeated_preferences_constraints`: repeated user sentences that look like preferences or constraints
- `unresolved_threads`: conversations whose last chronological message is still from the user

The heuristics are intentionally simple, local, deterministic, and easy to test. There are no network calls, embeddings, or model-generated summaries in this MVP.
