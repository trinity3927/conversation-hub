# Local search CLI implementation plan

> **For Hermes:** Use Codex and strict TDD to implement this plan.

**Goal:** Add the first usable local search command so the user can query stored conversation data immediately.

**Architecture:** Build a reusable SQLite search helper over the exported local database, then expose a thin `conversation-hub search` CLI that queries the database and prints deterministic JSON results to stdout. Keep the first version focused, local, and easy to test.

**Tech Stack:** Python 3.11, sqlite3, argparse, pathlib, json, pytest.

---

### Task 1: Add failing SQLite search tests

**Objective:** Define the SQLite search behavior before implementation.

**Files:**
- Create: `tests/test_storage_sqlite_search.py`

**Step 1: Write failing tests**
- Add a test that writes sample conversations into SQLite, runs a search query, and asserts:
  - query metadata is returned
  - matching conversations are returned in deterministic order
  - each result includes source, conversation id, title, message count, and an excerpt
- Add a test that respects `limit`.

**Step 2: Run tests to verify failure**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_storage_sqlite_search.py -q`
Expected: FAIL because the SQLite search module does not exist yet.

### Task 2: Implement reusable SQLite search helper

**Objective:** Add a reusable local search primitive over stored data.

**Files:**
- Create: `src/conversation_hub/storage/sqlite_search.py`
- Modify: `src/conversation_hub/storage/__init__.py`

**Step 1: Implement result model and query function**
- Add a structured result model, e.g. `SQLiteSearchResult`
- Add `search_conversations_sqlite(input_path, query, limit=10)`
- Search over at least:
  - conversation titles
  - content part text
- Return deterministic results with excerpts and counts.

**Step 2: Run focused tests**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_storage_sqlite.py tests/test_storage_sqlite_search.py -q`
Expected: PASS

### Task 3: Add failing CLI search test and wire the command

**Objective:** Expose a testable user-facing search command.

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/conversation_hub/cli.py`

**Step 1: Write failing CLI test**
- Add `test_search_command_prints_json_results_from_sqlite()`
- Assert `conversation-hub search --input <db> --query <text>`:
  - exits successfully
  - prints deterministic JSON to stdout
  - supports `--limit`

**Step 2: Run focused CLI test to verify failure**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_cli.py::test_search_command_prints_json_results_from_sqlite -q`
Expected: FAIL because the command is not implemented yet.

**Step 3: Implement CLI wiring**
- Add `search` subcommand
- Required args:
  - `--input`
  - `--query`
- Optional arg:
  - `--limit`
- Print JSON search results to stdout

**Step 4: Run focused tests**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_cli.py tests/test_storage_sqlite_search.py -q`
Expected: PASS

### Task 4: Update docs, tracking, and logs

**Objective:** Make the feature easy for the user to try immediately.

**Files:**
- Modify: `README.md`
- Create or modify: `docs/search-cli.md`
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Update docs**
- Document `conversation-hub search --input PATH --query QUERY [--limit N]`
- Include a quick example using the SQLite export output

**Step 2: Update tracking and logs**
- Update `to-do.md` to reflect that the first local search command exists
- Log failures, commands, results, and decisions in `logs/2026-03-16.md`

**Step 3: Run the full suite**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/ -q`
Expected: PASS
