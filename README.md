# conversation-hub

A Python project for pulling AI conversations from multiple sources, normalizing them into a common schema, organizing them for search/review, and running configurable actions on top of them.

## Initial goals

- Ingest conversations from multiple sources
- Normalize messages, participants, metadata, and attachments into one internal model
- Store conversations in a structured, queryable format
- Run downstream actions such as tagging, summarization, routing, extraction, or alerting
- Make it easy to add new connectors and action pipelines

## Proposed architecture

- `src/conversation_hub/connectors/`
  - source-specific importers (ChatGPT, Claude, Discord, Slack, email, etc.)
- `src/conversation_hub/models/`
  - normalized conversation/message schemas
- `src/conversation_hub/storage/`
  - local storage, indexing, and persistence adapters
- `src/conversation_hub/actions/`
  - post-processing actions and automation hooks
- `src/conversation_hub/pipelines/`
  - ingestion and processing orchestration
- `tests/`
  - project tests

## Example flow

1. Pull conversation exports or API payloads from a source
2. Convert them into a normalized internal representation
3. Store/index them
4. Run one or more configured actions
5. Expose results through a CLI or service layer

## Next good steps

- Decide the first 2-3 sources to support
- Define the normalized conversation schema
- Pick the first storage backend
- Define the first action types
- Build a CLI for importing and processing data
