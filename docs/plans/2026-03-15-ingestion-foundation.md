# Conversation Hub ingestion foundation plan

> Implementation note: follow strict TDD for this plan.

Goal: create the GitHub remote, strengthen the normalized conversation schema, and scaffold the first practical source connectors.

Architecture: keep the domain model vendor-neutral and make connectors translate source-specific exports into that model. Start with file-based export connectors for ChatGPT and Claude because they are concrete AI conversation sources and do not require live API credentials.

Tech stack: Python 3.11, dataclasses, pathlib, json, pytest.

---

1. Create or attach the GitHub remote for `your-org/conversation-hub`, push `main`, and confirm the remote URL.
2. Add tests that describe the normalized schema behavior we want:
   - messages can expose joined text content from structured parts
   - conversations can return messages in chronological order
   - timestamps from epoch seconds and ISO strings normalize cleanly
3. Implement the richer schema and normalization helpers needed to satisfy those tests.
4. Add tests for two first connectors using representative export payloads:
   - ChatGPT export connector reading `conversations.json`
   - Claude export connector reading a JSON export with embedded messages
5. Implement the connectors and any shared parsing helpers.
6. Run the focused tests, then the full test suite.
7. Commit the new model and connector foundation and push to GitHub.
