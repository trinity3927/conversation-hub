# Conversation Hub import CLI plan

> Implementation note: follow strict TDD for this plan.

Goal: add a real CLI import command that reads a supported source export, normalizes it through the existing connectors, and writes normalized JSON output.

Architecture: keep parsing inside connectors and keep CLI thin. Add a small JSON serialization layer for normalized conversations so the CLI can write a stable portable output without mixing serialization logic into argument parsing. Because this is a hackathon project, documentation is required as part of the feature, not as an optional follow-up.

Tech stack: Python 3.11+, argparse, pathlib, json, dataclasses, pytest.

---

1. Add CLI tests that define the desired behavior:
   - `conversation-hub import --source chatgpt --input ... --output ...` writes normalized JSON and exits successfully
   - `conversation-hub import --source claude ...` uses the Claude connector path
   - unsupported sources fail with a non-zero exit and a useful argparse error
2. Run the new focused CLI tests first and confirm they fail for the expected reason.
3. Implement the smallest CLI needed in `src/conversation_hub/cli.py` using `argparse` and a source-to-connector registry.
4. Add a small serialization helper, likely under `src/conversation_hub/storage/`, that converts `Conversation`, `Message`, `Participant`, and `ContentPart` into JSON-safe dictionaries with ISO-8601 timestamps.
5. Add thorough user-facing documentation:
   - update `README.md` with setup, supported sources, command examples, and normalized output notes
   - add a dedicated `docs/import-cli.md` reference covering command usage, arguments, examples, and output structure
   - add a concise architecture note describing connector -> normalization -> serialization flow
6. Run focused CLI tests, then the full suite.
7. Commit and push after verification.
