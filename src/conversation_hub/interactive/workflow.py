from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from conversation_hub.connectors import available_sources
from conversation_hub.interactive.browse import run_browse_session
from conversation_hub.models.schema import Conversation
from conversation_hub.pipelines import ImportResult, run_import
from conversation_hub.storage import (
    conversations_to_list,
    load_conversations_json,
    load_conversations_sqlite,
)


InputFn = Callable[[], str]
OutputFn = Callable[[object], None]
ImportRunner = Callable[[str, Path], ImportResult]
BrowseRunner = Callable[[list[Conversation], InputFn | None, OutputFn | None], None]
JSONLoadRunner = Callable[[Path], list[Conversation]]
SQLiteLoadRunner = Callable[[Path], list[Conversation]]

_WORKFLOW_OPTIONS = ("1", "2", "3", "q")
_DEFAULT_OUTPUT_DIRNAME = ".conversation-hub/normalized"


def run_browse_workflow(
    input_fn: InputFn | None = None,
    output_fn: OutputFn | None = None,
    default_data_dir: Path | None = None,
    import_runner: ImportRunner = run_import,
    browse_runner: BrowseRunner = run_browse_session,
    json_load_runner: JSONLoadRunner = load_conversations_json,
    sqlite_load_runner: SQLiteLoadRunner = load_conversations_sqlite,
) -> None:
    input_fn = input if input_fn is None else input_fn
    output_fn = print if output_fn is None else output_fn
    default_data_dir = Path.cwd() / _DEFAULT_OUTPUT_DIRNAME if default_data_dir is None else Path(default_data_dir)

    while True:
        output_fn("Browse launcher")
        output_fn("===============")
        output_fn("1. Open an existing normalized JSON file")
        output_fn("2. Import from a provider and browse it now")
        output_fn("3. Open a local SQLite export")
        output_fn("q. Quit")

        command = _read_command("Workflow command [1, 2, 3, q]:", input_fn, output_fn)

        if command == "q":
            output_fn("Quit workflow.")
            return

        if command == "1":
            conversations = _load_existing_conversations(
                input_fn=input_fn,
                output_fn=output_fn,
                load_runner=json_load_runner,
            )
            if conversations is not None:
                _open_browser(
                    conversations,
                    "normalized JSON",
                    input_fn,
                    output_fn,
                    browse_runner,
                )
                return
            continue

        if command == "2":
            conversations = _import_conversations_for_browse(
                input_fn=input_fn,
                output_fn=output_fn,
                default_data_dir=default_data_dir,
                import_runner=import_runner,
                json_load_runner=json_load_runner,
            )
            if conversations is not None:
                _open_browser(
                    conversations,
                    "normalized JSON",
                    input_fn,
                    output_fn,
                    browse_runner,
                )
                return
            continue

        if command == "3":
            conversations = _load_existing_sqlite_export(
                input_fn=input_fn,
                output_fn=output_fn,
                load_runner=sqlite_load_runner,
            )
            if conversations is not None:
                _open_browser(
                    conversations,
                    "SQLite export",
                    input_fn,
                    output_fn,
                    browse_runner,
                )
                return
            continue

        output_fn(f"Unrecognized command: {command or '(empty)'}")


def _load_existing_conversations(
    input_fn: InputFn,
    output_fn: OutputFn,
    load_runner: JSONLoadRunner,
) -> list[Conversation] | None:
    input_path = _read_required_path("Enter normalized JSON path:", input_fn, output_fn)

    try:
        return load_runner(input_path)
    except (OSError, ValueError) as exc:
        output_fn(f"Could not load normalized JSON: {exc}")
        return None


def _load_existing_sqlite_export(
    input_fn: InputFn,
    output_fn: OutputFn,
    load_runner: SQLiteLoadRunner,
) -> list[Conversation] | None:
    input_path = _read_required_path("Enter SQLite export path:", input_fn, output_fn)

    try:
        return load_runner(input_path)
    except (OSError, ValueError) as exc:
        output_fn(f"Could not load SQLite export: {exc}")
        return None


def _import_conversations_for_browse(
    input_fn: InputFn,
    output_fn: OutputFn,
    default_data_dir: Path,
    import_runner: ImportRunner,
    json_load_runner: JSONLoadRunner,
) -> list[Conversation] | None:
    source = _read_provider_choice(input_fn, output_fn)
    source_input_path = _read_required_path(f"Enter the source path for {source}:", input_fn, output_fn)
    output_path = _read_output_path(source, default_data_dir, input_fn, output_fn)

    try:
        result = import_runner(source, source_input_path)
        _write_normalized_json(result.conversations, output_path)
        output_fn(_format_import_summary(result, output_path))
        return json_load_runner(output_path)
    except (OSError, ValueError) as exc:
        output_fn(f"Could not import conversations: {exc}")
        return None


def _open_browser(
    conversations: list[Conversation],
    data_source_label: str,
    input_fn: InputFn,
    output_fn: OutputFn,
    browse_runner: BrowseRunner,
) -> None:
    conversation_count = len(conversations)
    output_fn(
        f"Opening browser for {conversation_count} "
        f"{_pluralize(conversation_count, 'conversation')} from {data_source_label}."
    )
    browse_runner(conversations, input_fn=input_fn, output_fn=output_fn)


def _write_normalized_json(conversations: list[Conversation], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = conversations_to_list(conversations)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _format_import_summary(result: ImportResult, output_path: Path) -> str:
    return (
        f"Imported {result.conversation_count} "
        f"{_pluralize(result.conversation_count, 'conversation')} "
        f"({result.message_count} {_pluralize(result.message_count, 'message')}) "
        f"from {result.source} to {output_path}"
    )


def _read_provider_choice(input_fn: InputFn, output_fn: OutputFn) -> str:
    providers = available_sources()
    provider_choices = ", ".join(providers)

    while True:
        provider = _read_text(f"Choose provider [{provider_choices}]:", input_fn, output_fn).lower()
        if provider in providers:
            return provider

        output_fn(f"Unrecognized provider: {provider or '(empty)'}")


def _read_output_path(
    source: str,
    default_data_dir: Path,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> Path:
    default_output_path = default_data_dir / f"{source}.json"
    raw_output_path = _read_text(
        f"Enter normalized output path [default: {default_output_path}]:",
        input_fn,
        output_fn,
    )

    return default_output_path if not raw_output_path else Path(raw_output_path)


def _read_required_path(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> Path:
    while True:
        raw_value = _read_text(prompt, input_fn, output_fn)
        if raw_value:
            return Path(raw_value)

        output_fn("A path is required.")


def _read_command(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    command = _read_text(prompt, input_fn, output_fn).lower()
    if command in _WORKFLOW_OPTIONS:
        return command
    return command


def _read_text(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn(prompt)
    return input_fn().strip()


def _pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
