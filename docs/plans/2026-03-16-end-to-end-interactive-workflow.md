# End-to-end interactive browse workflow plan

> Implementation note: follow strict TDD for this plan.

**Goal:** Make `conversation-hub browse` a no-required-args, end-to-end interactive workflow that can prompt for provider import, then visibly browse and analyze conversations in the terminal.

**Architecture:** Keep the CLI thin while expanding the interactive layer into a small workflow controller. `browse` should accept an optional `--input`; when omitted, it should launch an interactive setup flow that can import from a chosen provider into a local normalized JSON file and then immediately enter the browser session. The browser session should also gain more visible utility commands so the user can explore data without leaving the terminal.

**Tech Stack:** Python 3.11, argparse, pathlib, json, dataclasses, pytest, stdlib input/print.

---

### Task 1: Add failing workflow tests

**Objective:** Define the no-args interactive import-and-browse workflow before implementation.

**Files:**
- Create: `tests/test_interactive_workflow.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing tests**
- Add a workflow test with injected input/output functions that verifies:
  - no-input launch prompts the user to choose how to load data
  - the user can choose a provider (`chatgpt`, `claude`, `codex`)
  - the user can enter source path and output path interactively
  - the import runs and the browser opens automatically on the imported conversations
- Add a CLI test for `conversation-hub browse` with no `--input`, using `monkeypatch` on `builtins.input`.

**Step 2: Run tests to verify failure**
Run: `PYTHONPATH=src python -m pytest tests/test_interactive_workflow.py tests/test_cli.py::test_browse_command_without_input_runs_interactive_workflow -q`
Expected: FAIL because the interactive workflow controller does not exist yet.

### Task 2: Implement interactive workflow controller

**Objective:** Add the end-to-end visible import setup flow.

**Files:**
- Create: `src/conversation_hub/interactive/workflow.py`
- Modify: `src/conversation_hub/interactive/__init__.py`

**Step 1: Implement setup flow**
- Add a reusable function like `run_browse_workflow(input_fn=input, output_fn=print, default_data_dir=...)`
- Support at least:
  - open existing normalized JSON
  - import from provider and then browse
  - quit
- For provider import, prompt for:
  - source/provider
  - source input path
  - normalized output path (allow blank for a sensible default under local app data)
- After successful import, launch the existing browse session automatically.

**Step 2: Keep the flow visible**
- Print each step clearly in the terminal
- Show import summary before entering browse mode
- Keep everything stdlib-only and testable with injected I/O

**Step 3: Run focused tests**
Run: `PYTHONPATH=src python -m pytest tests/test_interactive_workflow.py tests/test_interactive_browse.py -q`
Expected: PASS

### Task 3: Improve browse session utility commands

**Objective:** Make browse mode more comprehensive for visible progress.

**Files:**
- Modify: `src/conversation_hub/interactive/browse.py`
- Modify: `tests/test_interactive_browse.py`

**Step 1: Add at least one more useful visible command**
- Add a main-list command such as:
  - `s` to show a short summary table again / expanded report
  - or `/` / `f` to filter conversations by keyword in-memory
- Add a selected-conversation command such as:
  - `d` for metadata/details dump
  - or `t` for tags/metadata/provenance view

**Step 2: Keep interaction readable and stable**
- Continue using explicit prompts
- Keep outputs deterministic for tests

**Step 3: Run focused tests**
Run: `PYTHONPATH=src python -m pytest tests/test_interactive_browse.py tests/test_cli.py -q`
Expected: PASS

### Task 4: Wire CLI browse to support both direct and no-args modes

**Objective:** Make `conversation-hub browse` the main interactive entrypoint.

**Files:**
- Modify: `src/conversation_hub/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Change browse args**
- Make `--input` optional
- If provided: load normalized JSON and launch the browse session directly
- If omitted: launch the interactive workflow controller

**Step 2: Run focused CLI tests**
Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_interactive_workflow.py tests/test_interactive_browse.py -q`
Expected: PASS

### Task 5: Update docs, tracking, and logs

**Objective:** Make the new end-to-end interactive workflow easy to try immediately.

**Files:**
- Modify: `README.md`
- Modify: `docs/browse-cli.md`
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Update docs**
- Document that `conversation-hub browse` can now be run without arguments
- Show the import-then-browse interactive path
- Document the new visible commands

**Step 2: Update tracking and logs**
- Update `to-do.md` to reflect the end-to-end interactive workflow
- Log failing tests, final test results, and design decisions in `logs/2026-03-16.md`

**Step 3: Run the full suite**
Run: `PYTHONPATH=src python -m pytest tests/ -q`
Expected: PASS
