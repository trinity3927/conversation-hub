# Interactive browse CLI implementation plan

> Implementation note: follow strict TDD for this plan.

**Goal:** Add a prompt-driven terminal browse mode so the user can visibly explore conversations, run an overall report, and trigger one-off analysis for a selected conversation.

**Architecture:** Keep normalized JSON as the interactive input format for the first version. Add a reusable interactive browser/session module that takes loaded `Conversation` objects plus injectable input/output functions for testing. Keep the CLI thin: parse args, load normalized conversations, and launch the browser session.

**Tech Stack:** Python 3.11, argparse, pathlib, json, dataclasses, pytest, stdlib input/print.

---

### Task 1: Add failing interactive browser tests

**Objective:** Define the visible interactive workflow before implementation.

**Files:**
- Create: `tests/test_interactive_browse.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing tests**
- Add a direct browser-session test using injected fake input/output functions that verifies:
  - the conversation list is shown
  - selecting a conversation displays conversation information
  - the user can trigger single-conversation analysis
  - the user can quit cleanly
- Add a CLI test for `conversation-hub browse --input <normalized.json>` using `monkeypatch` on `builtins.input`.

**Step 2: Run tests to verify failure**
Run: `PYTHONPATH=src python -m pytest tests/test_interactive_browse.py tests/test_cli.py::test_browse_command_runs_interactive_session -q`
Expected: FAIL because the interactive browser and CLI subcommand do not exist yet.

### Task 2: Implement reusable interactive browser module

**Objective:** Build the visible back-and-forth terminal workflow.

**Files:**
- Create: `src/conversation_hub/interactive/__init__.py`
- Create: `src/conversation_hub/interactive/browse.py`

**Step 1: Implement browser session**
- Add a function like `run_browse_session(conversations, input_fn=input, output_fn=print)`
- Show a list of conversations with stable numbering and summary data
- Support commands such as:
  - number = open conversation
  - `r` = overall report
  - `q` = quit
- In a selected conversation view, support:
  - `a` = analyze just this conversation
  - `m` = show messages
  - `b` = back
  - `q` = quit

**Step 2: Keep output human-readable**
- The session should visibly print information, not silently write files.
- Reuse `run_analysis()` for overall and one-conversation analysis, but render the output in a readable terminal format.

**Step 3: Run focused tests**
Run: `PYTHONPATH=src python -m pytest tests/test_interactive_browse.py -q`
Expected: PASS

### Task 3: Add CLI browse command

**Objective:** Expose the browser through the CLI without embedding session logic in `cli.py`.

**Files:**
- Modify: `src/conversation_hub/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Implement subcommand**
- Add `browse` subcommand with:
  - `--input` path to normalized JSON
- Load conversations via `load_conversations_json()`
- Call `run_browse_session()`

**Step 2: Run focused CLI tests**
Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_interactive_browse.py -q`
Expected: PASS

### Task 4: Update docs, tracking, and logs

**Objective:** Make the new visible CLI easy for the user to try immediately.

**Files:**
- Modify: `README.md`
- Create or modify: `docs/browse-cli.md`
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Update docs**
- Document `conversation-hub browse --input PATH`
- Include a quick interactive example with the commands the user can type

**Step 2: Update tracking and logs**
- Mark the first interactive browse mode as implemented in `to-do.md`
- Log test failures, commands, final results, and design decisions in `logs/2026-03-16.md`

**Step 3: Run the full suite**
Run: `PYTHONPATH=src python -m pytest tests/ -q`
Expected: PASS
