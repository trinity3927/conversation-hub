# SQLite storage export implementation plan

> Implementation note: follow strict TDD for this plan.

**Goal:** Add the first SQLite-backed local storage path by exporting normalized conversations into a deterministic SQLite database.

**Architecture:** Keep normalized JSON as the interchange format, then add a reusable SQLite storage writer that persists normalized conversations into a local database with explicit tables for conversations, participants, messages, and content parts. Keep the CLI thin by adding an export command that loads normalized conversations, dispatches to the SQLite writer, and prints a short summary.

**Tech Stack:** Python 3.11, sqlite3, dataclasses, argparse, pathlib, json, pytest.

---

### Task 1: Add failing SQLite storage tests

**Objective:** Define the storage layout and write behavior before implementation.

**Files:**
- Create: `tests/test_storage_sqlite.py`

**Step 1: Write failing tests**
- Add a test that writes a small normalized conversation set into SQLite and asserts:
  - the database file is created
  - expected tables exist
  - conversation, participant, message, and content part rows are inserted
  - timestamps and metadata are stored deterministically
- Add a test that writing the same dataset twice replaces the managed rows cleanly instead of duplicating them.

**Step 2: Run test to verify failure**
Run: `PYTHONPATH=src python -m pytest tests/test_storage_sqlite.py -q`
Expected: FAIL because the SQLite storage module does not exist yet.

### Task 2: Implement reusable SQLite storage writer

**Objective:** Add the default local storage backend.

**Files:**
- Create: `src/conversation_hub/storage/sqlite_store.py`
- Modify: `src/conversation_hub/storage/__init__.py`

**Step 1: Implement schema creation**
- Create explicit tables for at least:
  - `conversations`
  - `participants`
  - `messages`
  - `content_parts`
- Use stable primary keys and JSON text columns for metadata/tags where needed.

**Step 2: Implement write behavior**
- Add a reusable function such as `write_conversations_sqlite(conversations, output_path)`
- Ensure writes are deterministic and idempotent for the managed rows.
- Return a small structured result with conversation/message counts and output path.

**Step 3: Run focused storage tests**
Run: `PYTHONPATH=src python -m pytest tests/test_storage_sqlite.py tests/test_storage_json_import.py -q`
Expected: PASS

### Task 3: Add failing export CLI test and wire the command

**Objective:** Expose SQLite storage through the CLI while keeping orchestration thin.

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/conversation_hub/cli.py`

**Step 1: Write failing CLI test**
- Add `test_export_command_writes_sqlite_database()`
- Assert `conversation-hub export --format sqlite --input <normalized.json> --output <db>`:
  - exits successfully
  - creates the SQLite database
  - prints a short summary

**Step 2: Run focused CLI test to verify failure**
Run: `PYTHONPATH=src python -m pytest tests/test_cli.py::test_export_command_writes_sqlite_database -q`
Expected: FAIL because the command is not implemented yet.

**Step 3: Implement CLI wiring**
- Add `export` subcommand
- Add `--format` with `sqlite` as the initial supported value
- Load normalized conversations from JSON
- Call the reusable SQLite writer
- Print a concise summary

**Step 4: Run focused CLI and storage tests**
Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_storage_sqlite.py -q`
Expected: PASS

### Task 4: Update docs, project tracking, and logs

**Objective:** Keep the repo aligned with the new default local storage path.

**Files:**
- Modify: `README.md`
- Create or modify: `docs/export-cli.md`
- Modify: `docs/import-architecture.md` if it should mention the export/storage stage
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Update docs**
- Document `conversation-hub export --format sqlite --input PATH --output PATH`
- Document the SQLite tables at a high level

**Step 2: Update tracking**
- Mark default local SQLite storage as implemented in `to-do.md`
- Log TDD failures, commands, results, and design decisions in `logs/2026-03-16.md`

**Step 3: Run the full suite**
Run: `PYTHONPATH=src python -m pytest tests/ -q`
Expected: PASS
