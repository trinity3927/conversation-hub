from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

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

_DEFAULT_OUTPUT_DIRNAME = ".conversation-hub/normalized"
_DEFAULT_STATE_PATH = ".conversation-hub/state.json"
_HOME_ACTIONS = {"i", "j", "s", "q"}
_MAX_RECENT_DATASETS = 5


def run_browse_workflow(
    input_fn: InputFn | None = None,
    output_fn: OutputFn | None = None,
    default_data_dir: Path | None = None,
    state_path: Path | None = None,
    import_runner: ImportRunner = run_import,
    browse_runner: BrowseRunner = run_browse_session,
    json_load_runner: JSONLoadRunner = load_conversations_json,
    sqlite_load_runner: SQLiteLoadRunner = load_conversations_sqlite,
) -> None:
    input_fn = input if input_fn is None else input_fn
    output_fn = print if output_fn is None else output_fn
    default_data_dir = Path.cwd() / _DEFAULT_OUTPUT_DIRNAME if default_data_dir is None else Path(default_data_dir)
    state_path = Path.cwd() / _DEFAULT_STATE_PATH if state_path is None else Path(state_path)

    state = _load_state(state_path)

    while True:
        _render_home(state, output_fn)
        command = _read_command("Home command [recent number, i, j, s, q]:", input_fn, output_fn)

        if command == "q":
            output_fn("Quit workflow.")
            return

        if command == "i":
            result = _import_conversations_for_browse(
                state=state,
                input_fn=input_fn,
                output_fn=output_fn,
                default_data_dir=default_data_dir,
                import_runner=import_runner,
                json_load_runner=json_load_runner,
            )
            if result is None:
                continue

            conversations, dataset, state = result
            _save_state(state_path, state)
            _open_browser(
                conversations,
                "normalized JSON",
                input_fn,
                output_fn,
                browse_runner,
            )
            return

        if command == "j":
            result = _load_existing_conversations(
                state=state,
                input_fn=input_fn,
                output_fn=output_fn,
                load_runner=json_load_runner,
            )
            if result is None:
                continue

            conversations, dataset = result
            state = _register_recent_dataset(state, dataset)
            _save_state(state_path, state)
            _open_browser(
                conversations,
                "normalized JSON",
                input_fn,
                output_fn,
                browse_runner,
            )
            return

        if command == "s":
            result = _load_existing_sqlite_export(
                state=state,
                input_fn=input_fn,
                output_fn=output_fn,
                load_runner=sqlite_load_runner,
            )
            if result is None:
                continue

            conversations, dataset = result
            state = _register_recent_dataset(state, dataset)
            _save_state(state_path, state)
            _open_browser(
                conversations,
                "SQLite export",
                input_fn,
                output_fn,
                browse_runner,
            )
            return

        if command.isdigit():
            result = _load_recent_dataset(
                state=state,
                selection=int(command),
                output_fn=output_fn,
                json_load_runner=json_load_runner,
                sqlite_load_runner=sqlite_load_runner,
            )
            if result is None:
                continue

            conversations, dataset, data_source_label = result
            state = _register_recent_dataset(state, dataset)
            _save_state(state_path, state)
            _open_browser(
                conversations,
                data_source_label,
                input_fn,
                output_fn,
                browse_runner,
            )
            return

        output_fn(f"Unrecognized command: {command or '(empty)'}")


def _render_home(state: dict[str, Any], output_fn: OutputFn) -> None:
    _render_heading("Conversation Hub", output_fn)
    output_fn("Minimal home")
    output_fn("")
    _render_subheading("Recent datasets", output_fn)
    recent_datasets = _recent_datasets(state)
    if not recent_datasets:
        output_fn("(none)")
    else:
        for index, dataset in enumerate(recent_datasets, start=1):
            output_fn(f"{index}. {_dataset_label(dataset)}")
            output_fn(f"   {_dataset_descriptor(dataset)}")
            output_fn(f"   path: {dataset['path']}")

    output_fn("")
    _render_subheading("Remembered defaults", output_fn)
    output_fn(f"Last browse filter: {state.get('last_browse_filter') or '(none)'}")
    remembered_paths = _provider_paths(state)
    if not remembered_paths:
        output_fn("Provider paths: (none)")
    else:
        for provider in sorted(remembered_paths):
            output_fn(f"{provider}: {remembered_paths[provider]}")

    output_fn("")
    _render_subheading("Quick actions", output_fn)
    output_fn("i import provider export")
    output_fn("j open normalized JSON")
    output_fn("s open local SQLite export")
    output_fn("q quit")


def _load_existing_conversations(
    state: dict[str, Any],
    input_fn: InputFn,
    output_fn: OutputFn,
    load_runner: JSONLoadRunner,
) -> tuple[list[Conversation], dict[str, Any]] | None:
    input_path = _read_required_path("Enter normalized JSON path:", input_fn, output_fn)

    try:
        conversations = load_runner(input_path)
    except (OSError, ValueError) as exc:
        output_fn(f"Could not load normalized JSON: {exc}")
        return None

    dataset = _dataset_entry(
        kind="normalized_json",
        label=input_path.stem,
        path=input_path,
        provider=None,
        conversation_count=len(conversations),
    )
    return conversations, dataset


def _load_existing_sqlite_export(
    state: dict[str, Any],
    input_fn: InputFn,
    output_fn: OutputFn,
    load_runner: SQLiteLoadRunner,
) -> tuple[list[Conversation], dict[str, Any]] | None:
    input_path = _read_required_path("Enter SQLite export path:", input_fn, output_fn)

    try:
        conversations = load_runner(input_path)
    except (OSError, ValueError) as exc:
        output_fn(f"Could not load SQLite export: {exc}")
        return None

    dataset = _dataset_entry(
        kind="sqlite_export",
        label=input_path.stem,
        path=input_path,
        provider=None,
        conversation_count=len(conversations),
    )
    return conversations, dataset


def _load_recent_dataset(
    state: dict[str, Any],
    selection: int,
    output_fn: OutputFn,
    json_load_runner: JSONLoadRunner,
    sqlite_load_runner: SQLiteLoadRunner,
) -> tuple[list[Conversation], dict[str, Any], str] | None:
    recent_datasets = _recent_datasets(state)
    if selection < 1 or selection > len(recent_datasets):
        output_fn(f"Unrecognized command: {selection}")
        return None

    dataset = dict(recent_datasets[selection - 1])
    dataset_path = Path(str(dataset["path"]))
    try:
        if dataset.get("kind") == "sqlite_export":
            conversations = sqlite_load_runner(dataset_path)
            data_source_label = "SQLite export"
        else:
            conversations = json_load_runner(dataset_path)
            data_source_label = "normalized JSON"
    except (OSError, ValueError) as exc:
        output_fn(f"Could not open recent dataset: {exc}")
        return None

    dataset["conversation_count"] = len(conversations)
    return conversations, dataset, data_source_label


def _import_conversations_for_browse(
    state: dict[str, Any],
    input_fn: InputFn,
    output_fn: OutputFn,
    default_data_dir: Path,
    import_runner: ImportRunner,
    json_load_runner: JSONLoadRunner,
) -> tuple[list[Conversation], dict[str, Any], dict[str, Any]] | None:
    source = _read_provider_choice(input_fn, output_fn)
    raw_source_path = _read_provider_source_path(source, state, input_fn, output_fn)
    source_input_path = _resolve_source_input_path(source, raw_source_path, output_fn)
    output_path = _read_output_path(source, default_data_dir, input_fn, output_fn)

    try:
        result = import_runner(source, source_input_path)
        _write_normalized_json(result.conversations, output_path)
        output_fn(_format_import_summary(result, output_path))
        conversations = json_load_runner(output_path)
    except (OSError, ValueError) as exc:
        output_fn(f"Could not import conversations: {exc}")
        return None

    updated_state = dict(state)
    provider_paths = _provider_paths(updated_state)
    provider_paths[source] = str(raw_source_path)
    updated_state["last_provider_import_paths"] = provider_paths
    dataset = _dataset_entry(
        kind="normalized_json",
        label=f"{source} import",
        path=output_path,
        provider=source,
        conversation_count=len(conversations),
    )
    updated_state = _register_recent_dataset(updated_state, dataset)
    return conversations, dataset, updated_state


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


def _read_provider_source_path(
    source: str,
    state: dict[str, Any],
    input_fn: InputFn,
    output_fn: OutputFn,
) -> Path:
    remembered_path = _provider_paths(state).get(source)
    prompt = f"Enter source path for {source}:"
    if remembered_path:
        prompt = f"Enter source path for {source} [default: {remembered_path}]:"

    while True:
        raw_value = _read_text(prompt, input_fn, output_fn)
        if raw_value:
            return Path(raw_value)
        if remembered_path:
            return Path(remembered_path)
        output_fn("A path is required.")


def _resolve_source_input_path(source: str, source_path: Path, output_fn: OutputFn) -> Path:
    if source == "claude" and source_path.is_dir():
        detected_path = source_path / "conversations.json"
        if detected_path.is_file():
            output_fn(f"Detected Claude export file: {detected_path}")
            return detected_path
    return source_path


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
    return command


def _read_text(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn(prompt)
    return input_fn().strip()


def _load_state(state_path: Path) -> dict[str, Any]:
    default_state = {
        "last_browse_filter": None,
        "last_provider_import_paths": {},
        "recent_datasets": [],
    }
    if not state_path.exists():
        return default_state

    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default_state

    if not isinstance(payload, dict):
        return default_state

    state = dict(default_state)
    if payload.get("last_browse_filter") is not None:
        state["last_browse_filter"] = str(payload["last_browse_filter"])
    state["last_provider_import_paths"] = {
        str(provider): str(path)
        for provider, path in dict(payload.get("last_provider_import_paths", {})).items()
    }
    state["recent_datasets"] = [
        dict(dataset)
        for dataset in payload.get("recent_datasets", [])
        if isinstance(dataset, dict) and "path" in dataset and "kind" in dataset
    ]
    return state


def _save_state(state_path: Path, state: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _register_recent_dataset(state: dict[str, Any], dataset: dict[str, Any]) -> dict[str, Any]:
    updated_state = dict(state)
    recent_datasets = [
        existing
        for existing in _recent_datasets(updated_state)
        if not (
            str(existing.get("path")) == str(dataset.get("path"))
            and str(existing.get("kind")) == str(dataset.get("kind"))
        )
    ]
    recent_datasets.insert(0, dict(dataset))
    updated_state["recent_datasets"] = recent_datasets[:_MAX_RECENT_DATASETS]
    return updated_state


def _recent_datasets(state: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(dataset) for dataset in state.get("recent_datasets", []) if isinstance(dataset, dict)]


def _provider_paths(state: dict[str, Any]) -> dict[str, str]:
    raw_paths = state.get("last_provider_import_paths", {})
    if not isinstance(raw_paths, dict):
        return {}
    return {str(provider): str(path) for provider, path in raw_paths.items()}


def _dataset_entry(
    kind: str,
    label: str,
    path: Path,
    provider: str | None,
    conversation_count: int,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "label": label,
        "path": str(path),
        "provider": provider,
        "conversation_count": conversation_count,
    }


def _dataset_label(dataset: dict[str, Any]) -> str:
    label = dataset.get("label")
    if isinstance(label, str) and label:
        return label
    return Path(str(dataset["path"])).stem


def _dataset_descriptor(dataset: dict[str, Any]) -> str:
    conversation_count = int(dataset.get("conversation_count", 0))
    descriptor = (
        f"{dataset.get('kind', 'unknown')} | "
        f"{conversation_count} {_pluralize(conversation_count, 'conversation')}"
    )
    provider = dataset.get("provider")
    if provider:
        descriptor = f"{descriptor} | provider {provider}"
    return descriptor


def _render_heading(title: str, output_fn: OutputFn) -> None:
    output_fn(title)
    output_fn("=" * len(title))


def _render_subheading(title: str, output_fn: OutputFn) -> None:
    output_fn(title)
    output_fn("-" * len(title))


def _pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
