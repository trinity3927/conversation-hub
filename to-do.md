# conversation-hub macro to-do

This file tracks the project at a high level.
It should be kept current as the project evolves.

## Current product direction
- Build a system that pulls AI conversations from multiple sources
- Prefer official API / OAuth integrations
- Target UX is account-connected sync, not manual export upload
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
- File-based bootstrap connectors implemented
  - ChatGPT export connector
  - Claude export connector
- Import CLI implemented
  - `conversation-hub import --source {chatgpt,claude} --input PATH --output PATH`
- JSON serialization for normalized output implemented
- Tests added for schema, connectors, CLI, and serialization
- Development logging started in `logs/`

## Now
- Define the official account-connected ingestion architecture
- Clarify source scope for OpenAI
  - ChatGPT personal history?
  - OpenAI developer/API-side resources?
- Design source/account model for connected providers
- Design sync run model and sync logging flow

## Next
- Add provider registry for official integrations
- Add auth model
  - oauth
  - api key
  - token metadata / status
- Add `conversation-hub sync ...` CLI skeleton
- Add first official provider connector
- Add durable local storage for synced normalized conversations

## Later
- Add action pipelines
  - summarization
  - tagging
  - extraction
  - routing / alerts
- Add more providers
- Add dedupe / incremental sync
- Add search / indexing
- Add better operator UX around connection + sync status
- Finalize polished project documentation

## Open questions
- What exact official providers should be supported first?
- What counts as a "conversation" across different providers?
- How should account credentials/tokens be stored locally?
- Should sync be one-shot, scheduled, or both?
