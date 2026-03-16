# Import pipeline boundary implementation plan

> **For Hermes:** Use Codex and strict TDD to implement this plan.

**Goal:** Add an explicit reusable import pipeline boundary so source resolution, connector execution, and normalized import results are no longer embedded directly in the CLI.

**Architecture:** Move source registration into a shared connector registry and add a small import pipeline module that resolves a source, runs the connector, and returns normalized conversations plus summary counts. Keep the CLI thin: parse args, call the pipeline, serialize results, write output, print summary.

**Tech Stack:** Python 3.11, argparse, pathlib, dataclasses, pytest.

---

### Task 1: Add failing import pipeline tests

**Objective:** Define the reusable import behavior before implementation.

**Files:**
- Create: `tests/test_import_pipeline.py`
- Modify: `tests/test_cli.py` only if the CLI assertions need to reflect the new shared pipeline path

**Step 1: Write failing tests**
- Add `test_run_import_returns_conversations_and_counts_for_chatgpt()`
- Add `test_run_import_supports_codex_directory_inputs()`
- Assert that the pipeline returns:
  - normalized `Conversation` objects
  - `conversation_count`
  - `message_count`
  - source name and input path metadata

**Step 2: Run test to verify failure**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_import_pipeline.py -q`
Expected: FAIL because the pipeline module does not exist yet.

**Step 3: Do not implement production code yet**
- Stop after confirming the tests fail for the expected reason.

### Task 2: Add connector registry and import pipeline

**Objective:** Create the reusable boundary that the CLI will call.

**Files:**
- Create: `src/conversation_hub/connectors/registry.py`
- Create: `src/conversation_hub/pipelines/import_pipeline.py`
- Modify: `src/conversation_hub/connectors/__init__.py`
- Modify: `src/conversation_hub/pipelines/__init__.py`

**Step 1: Implement the shared connector registry**
- Export one authoritative source registry covering `chatgpt`, `claude`, and `codex`
- Add helper accessors such as `get_connector_class()` and/or `available_sources()` if useful

**Step 2: Implement the import pipeline**
- Add a small result model, e.g. `ImportResult`
- Add `run_import(source: str, input_path: Path) -> ImportResult`
- Resolve the connector from the shared registry
- Materialize normalized conversations once
- Compute conversation/message counts in the pipeline

**Step 3: Run focused tests**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_import_pipeline.py tests/test_connectors.py -q`
Expected: PASS

### Task 3: Refactor the CLI to use the pipeline

**Objective:** Keep the CLI thin and make it consume the reusable import boundary.

**Files:**
- Modify: `src/conversation_hub/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Update the CLI**
- Use the shared registry for argparse `choices`
- Call `run_import()` instead of instantiating connectors directly
- Serialize `ImportResult.conversations`
- Print the summary using `ImportResult.conversation_count` and `ImportResult.message_count`

**Step 2: Run focused tests**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/test_cli.py tests/test_import_pipeline.py -q`
Expected: PASS

### Task 4: Refresh docs and logs

**Objective:** Capture the new boundary so future work can build on it.

**Files:**
- Modify: `README.md`
- Modify: `docs/import-architecture.md`
- Modify: `docs/import-cli.md`
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Update docs**
- Explain that import resolution/execution now lives in a reusable pipeline layer
- Keep CLI docs explicit and scriptable

**Step 2: Update project tracking**
- Mark normalization pipeline boundaries as done in `to-do.md`
- Log commands, failures, final test results, and decisions in `logs/2026-03-16.md`

**Step 3: Run the full suite**
Run: `PYTHONPATH=src /home/sindri/.hermes/hermes-agent/venv/bin/python -m pytest tests/ -q`
Expected: PASS
