# Codex local-state importer implementation plan

> For Hermes: follow strict TDD for each code change.

Goal: add a third real importer for Codex CLI local session state so conversation-hub can ingest local-first agent history, not just exported provider files.

Architecture: keep the CLI thin and extend the connector layer with a Codex-specific local-state connector that can read either a single Codex session JSONL file or a `.codex` state directory. Normalize Codex session metadata plus user/assistant messages into the shared conversation schema while preserving provenance in metadata.

Tech stack: Python 3.11, pathlib, json, dataclasses, argparse, pytest.

---

1. Add failing connector tests for Codex local state:
   - a `.codex/sessions/.../*.jsonl` session file can be parsed into one normalized conversation
   - a `.codex` root directory can be scanned for multiple session files
   - user and assistant messages are preserved in chronological order
   - session/source metadata is stored on the conversation
2. Run the focused Codex connector tests and confirm failure.
3. Implement the Codex connector in `src/conversation_hub/connectors/` with minimal helpers for:
   - locating session JSONL files from a file or `.codex` directory input
   - loading JSONL events safely
   - extracting session metadata and normalized user/assistant messages
4. Add failing CLI tests for `conversation-hub import --source codex --input <path> --output <path>`.
5. Run the focused CLI Codex tests and confirm failure.
6. Register the Codex connector in the connector package and CLI registry.
7. Run focused Codex connector + CLI tests, then the full suite.
8. Update `README.md`, `to-do.md`, and `logs/2026-03-16.md` with the new importer and decisions.
