# Import architecture

The import flow is intentionally split into three small layers so source parsing, domain normalization, and JSON output stay separate.

## Flow

1. The CLI parses `--source`, `--input`, and `--output` with `argparse`.
2. A source registry selects the connector class for the chosen source.
3. The connector reads the source export and yields normalized `Conversation` objects built from `Conversation`, `Message`, `Participant`, and `ContentPart`.
4. The JSON serialization helper converts those models into JSON-safe dictionaries with ISO-8601 timestamps.
5. The CLI writes the serialized list to disk and prints a short import summary.

## Responsibilities

- `src/conversation_hub/cli.py`: argument parsing, source selection, file writing, summary output
- `src/conversation_hub/connectors/`: source-specific parsing and normalization into the shared schema
- `src/conversation_hub/models/schema.py`: normalized dataclasses and timestamp normalization
- `src/conversation_hub/storage/json_export.py`: JSON-safe serialization for normalized models

## Why this boundary

Keeping serialization out of the connectors avoids baking output-format decisions into source adapters. Keeping source parsing out of the CLI keeps the command thin and makes new sources a registry change plus a connector implementation instead of CLI-specific branching.
