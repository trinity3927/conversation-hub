# Default analysis outputs implementation plan

> Implementation note: follow strict TDD for this plan.

**Goal:** Add a first `conversation-hub analyze` command that reads normalized conversation JSON and writes a deterministic analysis report covering the handover's default output categories.

**Architecture:** Add a normalized JSON loader, then build a reusable analysis pipeline that works on `Conversation` objects and returns a structured report. Keep the CLI thin: parse args, load normalized conversations through the pipeline, write analysis JSON, and print a short summary.

**Tech Stack:** Python 3.11, dataclasses, argparse, pathlib, json, re, collections, pytest.

---

### Task 1: Add failing loader and analysis pipeline tests

**Objective:** Define the normalized-input analysis behavior before implementation.

**Files:**
- Create: `tests/test_analysis_pipeline.py`
- Create or modify: `tests/test_storage_json_import.py`

**Step 1: Write failing tests**
- Add a round-trip style test that loads normalized conversation JSON into `Conversation` objects.
- Add an analysis test that asserts the report includes:
  - `summary` with conversation/message counts
  - `source_patterns`
  - `recurring_projects_goals`
  - `important_entities`
  - `reusable_prompts`
  - `repeated_preferences_constraints`
  - `unresolved_threads`
- Use deterministic sample data with repeated project/prompt/constraint language so the expected report is easy to assert.

**Step 2: Run test to verify failure**
Run: `PYTHONPATH=src python -m pytest tests/test_analysis_pipeline.py tests/test_storage_json_import.py -q`
Expected: FAIL because the loader and/or analysis pipeline do not exist yet.

### Task 2: Implement normalized JSON loading and analysis pipeline

**Objective:** Build the reusable analysis boundary.

**Files:**
- Create: `src/conversation_hub/storage/json_import.py`
- Modify: `src/conversation_hub/storage/__init__.py`
- Create: `src/conversation_hub/pipelines/analyze_pipeline.py`
- Modify: `src/conversation_hub/pipelines/__init__.py`

**Step 1: Implement normalized JSON loading**
- Add helpers to convert normalized JSON dicts back into `Participant`, `ContentPart`, `Message`, and `Conversation` objects.
- Add a loader for a normalized JSON file containing a list of conversations.

**Step 2: Implement analysis pipeline**
- Add a structured result model, e.g. `AnalysisResult`
- Add `run_analysis(conversations: list[Conversation]) -> AnalysisResult`
- Include deterministic heuristic sections:
  - `summary`
  - `source_patterns`
  - `recurring_projects_goals`
  - `important_entities`
  - `reusable_prompts`
  - `repeated_preferences_constraints`
  - `unresolved_threads`
- Keep heuristics simple, local, and testable.

**Step 3: Run focused tests**
Run: `PYTHONPATH=src python -m pytest tests/test_analysis_pipeline.py tests/test_storage_json_import.py -q`
Expected: PASS

### Task 3: Add failing CLI analysis test and wire the command

**Objective:** Expose analysis through the CLI without moving business logic into the CLI.

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/conversation_hub/cli.py`

**Step 1: Write failing CLI test**
- Add `test_analyze_command_writes_analysis_report()`
- Assert `conversation-hub analyze --input <normalized.json> --output <report.json>`:
  - exits successfully
  - writes the expected report structure
  - prints a short summary line

**Step 2: Run the focused CLI analysis test**
Run: `PYTHONPATH=src python -m pytest tests/test_cli.py::test_analyze_command_writes_analysis_report -q`
Expected: FAIL because the command is not implemented yet.

**Step 3: Implement the CLI wiring**
- Add `analyze` subcommand
- Load normalized conversations from JSON
- Call the analysis pipeline
- Write analysis JSON output
- Print a concise summary

**Step 4: Run focused CLI + pipeline tests**
Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_analysis_pipeline.py tests/test_storage_json_import.py -q`
Expected: PASS

### Task 4: Update docs, project tracking, and logs

**Objective:** Keep repo documentation and tracking aligned with the new MVP step.

**Files:**
- Modify: `README.md`
- Create or modify: `docs/analyze-cli.md`
- Modify: `docs/import-architecture.md` only if it should reference the analysis stage
- Modify: `to-do.md`
- Modify: `logs/2026-03-16.md`

**Step 1: Update docs**
- Document the `analyze` command and its JSON report shape.
- Keep the command explicit and scriptable.

**Step 2: Update project tracking**
- Mark the first default analysis outputs as implemented in `to-do.md`.
- Log test commands, failures, final results, and decisions in `logs/2026-03-16.md`.

**Step 3: Run the full suite**
Run: `PYTHONPATH=src python -m pytest tests/ -q`
Expected: PASS
