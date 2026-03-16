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
- Import CLI implemented
  - `conversation-hub import --source {chatgpt,claude} --input PATH --output PATH`
- JSON serialization for normalized output implemented
- Tests added for schema, connectors, CLI, and serialization
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
- Implement a third real importer focused on local-first state
  - Codex CLI local state
  - or another CLI tool with real local session files
- Add normalization pipeline boundaries
- Add default analysis outputs
  - recurring projects/goals
  - important entities/repos/products
  - reusable prompts/workflows
  - repeated preferences/constraints
  - unresolved threads
- Add default local storage in SQLite
- Add local search/report/export commands

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
- Which local-first importer should be the 3rd solid source after ChatGPT and Claude?
- What exact canonical entities should be first-class in the schema now versus later?
- What should the first memory extraction outputs look like in the CLI?
- What should the default SQLite layout be?
