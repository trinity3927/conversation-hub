# Import architecture

The import, analysis, and local export flow is intentionally split into small layers so source registration, connector execution, domain normalization, JSON serialization, JSON loading, heuristic analysis, and storage writing stay separate across both export files and local state inputs.

## Flow

1. The CLI parses `--source`, `--input`, and `--output` with `argparse`.
2. The shared connector registry resolves the connector class for the chosen source.
3. The import pipeline runs the connector once, materializes normalized `Conversation` objects, and computes conversation/message counts in an `ImportResult`.
4. The JSON serialization helper converts `ImportResult.conversations` into JSON-safe dictionaries with ISO-8601 timestamps.
5. The CLI writes the serialized list to disk and prints a short import summary from the pipeline result.
6. The analysis CLI loads normalized JSON back into `Conversation` objects through the JSON import helper.
7. The analysis pipeline computes deterministic heuristic sections over those normalized conversations.
8. The CLI writes the report JSON and prints a short analysis summary.
9. The export CLI also loads normalized JSON back into `Conversation` objects through the JSON import helper.
10. The SQLite storage writer persists those conversations into explicit local tables for conversations, participants, messages, and content parts.
11. The CLI prints a short export summary from the storage result.

## Responsibilities

- `src/conversation_hub/cli.py`: argument parsing, output file writing, summary output
- `src/conversation_hub/connectors/registry.py`: authoritative source registration shared by the CLI and pipelines
- `src/conversation_hub/connectors/`: source-specific parsing and normalization into the shared schema
- `src/conversation_hub/models/schema.py`: normalized dataclasses and timestamp normalization
- `src/conversation_hub/pipelines/import_pipeline.py`: source resolution, connector execution, and import summary counts
- `src/conversation_hub/pipelines/analyze_pipeline.py`: deterministic heuristic analysis over normalized conversations
- `src/conversation_hub/storage/json_import.py`: loading normalized JSON back into shared dataclasses
- `src/conversation_hub/storage/json_export.py`: JSON-safe serialization for normalized models
- `src/conversation_hub/storage/sqlite_store.py`: deterministic SQLite schema creation and managed-row rewrites for normalized conversations

## Why this boundary

Keeping serialization out of the connectors avoids baking output-format decisions into source adapters. Keeping source resolution and execution out of the CLI keeps the commands thin and makes new sources a registry change plus a connector implementation instead of CLI-specific branching. The current normalized JSON boundary also gives future analysis, storage, or batch workflows reusable import and load entrypoints instead of re-implementing connector lookup, normalized loading, report generation, or SQLite persistence logic.
