# Interactive CLI polish plan

> **For Hermes:** Use Codex and strict TDD to implement this plan.

**Goal:** Make the interactive CLI feel substantially more visible, guided, and polished, while keeping the workflow fully end-to-end from import/load through browsing and per-conversation analysis.

**Architecture:** Keep `conversation-hub browse` as the main entrypoint, but improve the interactive workflow and session rendering. Add clearer on-screen command help, richer conversation previews, integrated interactive search/filter behavior, and support opening from either normalized JSON or SQLite. Keep CLI parsing thin and put behavior in reusable interactive modules.

**Tech Stack:** Python 3.11, argparse, pathlib, sqlite3, json, dataclasses, pytest, stdlib input/print.

---

### Task 1: Add failing polish tests

**Objective:** Lock in the improved visible behavior before implementation.

**Files:**
- Modify: `tests/test_interactive_browse.py`
- Modify: `tests/test_interactive_workflow.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing tests**
- Add assertions that the browser explicitly prints command help in both main-list and conversation views.
- Add a test for richer conversation preview rows including title, source, message count, and a short excerpt/preview.
- Add a workflow test for opening from SQLite as well as normalized JSON/provider import.
- Add a CLI test that `conversation-hub browse` no-args mode visibly offers all entry options.

**Step 2: Run focused tests to verify failure**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_interactive_browse.py tests/test_interactive_workflow.py tests/test_cli.py -q`
Expected: FAIL because the current UI is not polished enough yet.

### Task 2: Improve session presentation and discoverability

**Objective:** Make the browser self-explanatory and nicer to use.

**Files:**
- Modify: `src/conversation_hub/interactive/browse.py`

**Step 1: Add visible help text**
- Print command help every time the user enters:
  - main list view
  - selected conversation view
- Use explicit text like:
  - `[number] open conversation`
  - `r overall report`
  - `f filter`
  - `q quit`
  - etc.

**Step 2: Improve formatting**
- Add clearer section separators and headings
- Add short conversation previews/excerpts in the list
- Make reports easier to scan in-terminal

**Step 3: Add at least one more useful visible command**
- Examples:
  - `s` for a structured summary panel
  - `t` for metadata/tags/provenance on selected conversation
  - `n` / `c` for next/back to list pages if pagination becomes necessary

**Step 4: Run focused tests**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_interactive_browse.py -q`
Expected: PASS

### Task 3: Expand entry workflow options

**Objective:** Make browse truly end-to-end and flexible from the first prompt.

**Files:**
- Modify: `src/conversation_hub/interactive/workflow.py`
- Modify: `src/conversation_hub/storage/sqlite_search.py` only if a tiny helper is useful

**Step 1: Support multiple entry paths clearly**
- Main workflow should visibly offer:
  - open normalized JSON
  - import from provider now
  - open SQLite export
  - quit

**Step 2: Add SQLite-backed browse entry**
- Prompt for SQLite path
- Load conversations from SQLite into a browsable in-memory representation or use a reusable loader/helper
- Enter the same browse session after loading

**Step 3: Run focused workflow tests**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_interactive_workflow.py -q`
Expected: PASS

### Task 4: Keep CLI thin and update docs/logs

**Objective:** Preserve architecture while making the improved flow easy to try immediately.

**Files:**
- Modify: `src/conversation_hub/cli.py`
- Modify: `README.md`
- Modify: `docs/browse-cli.md`
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Ensure CLI stays thin**
- `browse` should still only parse args and dispatch into interactive modules.

**Step 2: Update docs**
- Document the no-args end-to-end flow
- Document direct browse from normalized JSON and SQLite if implemented
- Document visible commands shown in the UI

**Step 3: Run full suite**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/ -q`
Expected: PASS
