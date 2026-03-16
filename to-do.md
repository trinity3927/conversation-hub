# conversation-hub macro to-do

This file tracks the project at a high level.
It should be kept current as the project evolves.

## Current product direction
- Build a local-first conversation ETL + memory extraction tool for AI chats
- Primary value: universal ingestion + normalization + memory extraction
- CLI-first MVP
- Start with simple, reliable ingestion flows
  - manual export import
  - local folder scanning
  - provider-specific adapters
- Do not make account-linking / sync / hosted infra the MVP path
- During development, log everything
- Polished top-level docs can be finalized later

## Done
- Repository initialized and pushed to GitHub
- Core normalized schema implemented
  - Participant
  - ContentPart
  - Message
  - Conversation
  - normalize_timestamp
- File-based importers implemented
  - ChatGPT export connector
  - Claude export connector
  - Codex CLI local-state connector
- Import CLI implemented
  - `conversation-hub import --source {chatgpt,claude,codex} --input PATH --output PATH`
- Shared connector registry implemented for import sources
- Reusable import pipeline boundary implemented
  - resolves a source from the registry
  - runs the connector
  - returns normalized conversations plus conversation/message counts
- JSON serialization for normalized output implemented
- Normalized JSON loading implemented
  - reconstructs `Conversation`, `Message`, `Participant`, and `ContentPart` objects from normalized JSON
- Reusable analysis pipeline implemented
  - returns deterministic default outputs for summary counts, source patterns, recurring projects/goals, important entities, reusable prompts, repeated preferences/constraints, and unresolved threads
- Analyze CLI implemented
  - `conversation-hub analyze --input PATH --output PATH`
- Default local SQLite storage implemented
  - reusable `write_conversations_sqlite()` writer for deterministic `conversations`, `participants`, `messages`, and `content_parts` tables
- Export CLI implemented
  - `conversation-hub export --format sqlite --input PATH --output PATH`
- Tests added for schema, connectors, import pipeline, analysis pipeline, CLI, serialization, and normalized JSON loading
- Development logging started in `logs/`
- Added high-level project tracker in `to-do.md`

## Now
- Align the repo with the handover direction as the authoritative prompt
- Preserve useful existing work while reframing the MVP around ingestion + normalization + memory extraction
- Define one durable canonical schema that can grow toward:
  - sources
  - conversations
  - messages
  - artifacts
  - entities
  - memories
- Add macro tracking for the fastest CLI-first MVP path

## Next
- Add importer/adapter system explicitly oriented around:
  - exported files/folders
  - local CLI state folders
  - provider-specific parsers
- Add local search/report commands over normalized JSON and SQLite storage
- Add additional export targets after SQLite proves out

## Later
- Add optional embeddings/vector layer
  - sqlite-vec first if needed
  - pgvector export later
- Add Postgres export
- Add more providers with confidence-aware adapters
- Add optional watcher/sync modes only after core ingestion is solid
- Add better operator UX
- Finalize polished project documentation

## Anti-goals for now
- Managed vector DB as core product identity
- Complicated account-linking flows as MVP onboarding
- Browser automation as primary ingestion path
- Remote/multi-device orchestration as a core requirement
- Over-engineered memory systems before ingestion is reliable

## Open questions
- What exact canonical entities should be first-class in the schema now versus later?
- What should the first memory extraction outputs look like in the CLI?
- What should the next export target after SQLite be?
