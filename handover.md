# this project handover

This file is the current high-level handover for the this project CLI agent.
Where it conflicts with older notes or earlier assumptions, **follow this file**.

## What this project is
this project is a **local-first conversation ETL + memory extraction tool for AI chats**.
Its job is to ingest LLM conversations from many providers, normalize them into one schema, extract useful memory, and make the result searchable and exportable for future agents.

## The problem
Power users have conversations spread across products like ChatGPT, Claude, Codex CLI, Gemini CLI, Perplexity, Grok, and others.
Those conversations are valuable, but fragmented, hard to search, hard to reuse, and not in a form that other agents can reliably consume.

## Product thesis
The core product is **not** “build a vector DB from chats.”
The core product is:
1. ingest conversations from many sources,
2. normalize them into one canonical format,
3. extract durable memory / patterns / artifacts,
4. let the user search, review, and export the results.

Embeddings and vector search are optional enhancements, not the product identity.

## What changed / clarified today
Earlier thinking leaned too much toward “database provider + vector DB” as the main outcome.
That is no longer the framing.

Current framing:
- **primary value:** universal ingestion + normalization + memory extraction
- **default output:** useful summaries, memories, reusable prompts, unresolved threads, recurring projects/preferences
- **secondary output:** optional export into SQLite / JSONL / Postgres / vector-backed storage

## MVP direction
Build this project as a **CLI-first** tool.
A GUI is optional later; do not let GUI work slow down the core pipeline.

### MVP should do
- import conversation data from multiple providers
- normalize to a canonical schema
- run useful analysis over the imported data
- provide local search / reporting / export

### MVP should not depend on
- hosted infrastructure
- a managed vector DB
- complicated account-linking flows
- cross-device remote ingestion as a requirement

## Recommended initial ingestion strategy
Start with the simplest, most reliable flows first:

1. **manual export import**
   - user exports their data from the provider
   - this project ingests the exported files/folders

2. **local folder scanning**
   - for CLI agents or tools that store state locally
   - this project scans known paths or user-provided paths

3. **provider-specific adapters**
   - per-source parsers with version-aware logic

4. **advanced modes later**
   - cross-device linking
   - SSH / remote retrieval
   - automatic watchers / sync

Do **not** make SSH/device-link mode the default onboarding path.
It is powerful, but too complex and high-friction for MVP.

## Important source-specific guidance
Treat provider support with different confidence levels.

### High-confidence foundations
- **ChatGPT:** user-triggered export flow exists; design around import of exported data
- **Claude:** user-triggered export flow exists; design around import of exported data
- **Codex CLI:** local-first state is real; importer should handle local state carefully and be version-aware
- **Gemini CLI / other CLI tools:** expect local session/checkpoint/state patterns rather than account-level cloud export

### Lower-confidence / careful handling
- **Perplexity / Grok / similar products:** do not hard-code assumptions about full account-level export unless confirmed in current docs or observed from real user data
- support them via flexible adapters, thread exports, scraped formats, or manual file ingestion first

## Canonical data model
Keep the schema simple and durable.
Suggested core entities:
- `sources`
- `conversations`
- `messages`
- `artifacts`
- `entities`
- `memories`
- optional `embeddings`

The canonical format should preserve:
- provider/source metadata
- timestamps
- roles
- message content
- attached artifacts/files if available
- conversation/thread grouping
- provenance back to original source

## Default value this project should produce
If the user imports data and asks this project to “analyze it,” the default output should emphasize:
- recurring projects and goals
- important people / entities / repos / products mentioned often
- reusable prompts and workflows
- repeated preferences or constraints
- unresolved threads / abandoned tasks
- source-by-source patterns (which provider was useful for what)

This is stronger than generic scoring.

## Storage direction
Default storage should be **SQLite**.
That keeps this project local-first, simple, and hackathon-friendly.

Recommended progression:
- default: plain SQLite
- optional local vector layer: `sqlite-vec`
- optional Postgres export: `pgvector`
- only later consider Qdrant / other vector-native backends if the use case clearly needs it

## UX direction
this project should feel like a sharp CLI tool for technical users.
Example command surface:
- `conversation-hub import chatgpt <export>`
- `conversation-hub import claude <export>`
- `conversation-hub import codex <path>`
- `conversation-hub analyze`
- `conversation-hub memories build`
- `conversation-hub search <query>`
- `conversation-hub export --format sqlite|jsonl|markdown|pg`

Keep the interface explicit and scriptable.

## Build order
1. define canonical schema
2. build importer interface / adapter system
3. implement 2–3 real importers first
   - ChatGPT export
   - Claude export
   - Codex/local CLI state
4. build normalization pipeline
5. build default analysis outputs
6. build local search
7. add optional embeddings/export targets
8. only then consider GUI or remote/device-link features

## Decision principles
When choosing between options, prefer:
- local-first over hosted-first
- simple import flows over magical sync
- durable normalized data over fancy demos
- clear provenance over opaque transformations
- useful analysis over vague “AI insights”

## Anti-goals for now
Avoid drifting into these too early:
- full collaboration platform
- enterprise sync product
- browser automation as the core ingestion method
- remote agent orchestration across many machines
- over-engineered memory systems before reliable ingestion exists

## What the CLI agent should do next
1. inspect the repo and preserve any useful prior work
2. compare existing work against this handover
3. align the project around the CLI-first ingestion/normalization direction
4. identify the fastest path to a working MVP
5. prioritize one canonical schema and a small number of solid importers over broad but weak coverage

## North star
this project should become the easiest way for a power user to turn scattered AI conversations into **clean, portable, searchable memory**.
