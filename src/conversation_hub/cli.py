from __future__ import annotations

import argparse
import json
from pathlib import Path

from conversation_hub.connectors import available_sources
from conversation_hub.interactive import run_browse_session
from conversation_hub.pipelines import run_analysis, run_import
from conversation_hub.storage import (
    conversations_to_list,
    load_conversations_json,
    search_conversations_sqlite,
    write_conversations_sqlite,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conversation-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a conversation export into normalized JSON")
    import_parser.add_argument(
        "--source",
        required=True,
        choices=available_sources(),
        help="Connector source to use for the input export",
    )
    import_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the source export file or local state directory",
    )
    import_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the normalized JSON file",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze normalized conversations and write a deterministic JSON report",
    )
    analyze_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a normalized JSON conversation file",
    )
    analyze_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the JSON analysis report",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Export normalized conversations into a local storage format",
    )
    export_parser.add_argument(
        "--format",
        required=True,
        choices=["sqlite"],
        help="Output format for the normalized conversations",
    )
    export_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a normalized JSON conversation file",
    )
    export_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the exported output",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search a local SQLite export and print deterministic JSON results",
    )
    search_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a local SQLite conversation export",
    )
    search_parser.add_argument(
        "--query",
        required=True,
        type=_non_empty_string,
        help="Case-insensitive text to search in conversation titles and content",
    )
    search_parser.add_argument(
        "--limit",
        default=10,
        type=_positive_int,
        help="Maximum number of matches to return",
    )

    browse_parser = subparsers.add_parser(
        "browse",
        help="Browse normalized conversations in an interactive terminal session",
    )
    browse_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a normalized JSON conversation file",
    )

    return parser


def _run_import(source: str, input_path: Path, output_path: Path) -> int:
    result = run_import(source, input_path)
    payload = conversations_to_list(result.conversations)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(
        f"Imported {result.conversation_count} "
        f"{_pluralize(result.conversation_count, 'conversation')} "
        f"({result.message_count} {_pluralize(result.message_count, 'message')}) "
        f"from {result.source} to {output_path}"
    )
    return 0


def _run_analyze(input_path: Path, output_path: Path) -> int:
    conversations = load_conversations_json(input_path)
    report = run_analysis(conversations).to_dict()
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    message_count = report["summary"]["message_count"]
    conversation_count = report["summary"]["conversation_count"]
    print(
        f"Analyzed {conversation_count} "
        f"{_pluralize(conversation_count, 'conversation')} "
        f"({message_count} {_pluralize(message_count, 'message')}) "
        f"from {input_path} to {output_path}"
    )
    return 0


def _run_export(format_name: str, input_path: Path, output_path: Path) -> int:
    conversations = load_conversations_json(input_path)

    if format_name == "sqlite":
        result = write_conversations_sqlite(conversations, output_path)
    else:
        raise ValueError(f"Unsupported export format: {format_name}")

    print(
        f"Exported {result.conversation_count} "
        f"{_pluralize(result.conversation_count, 'conversation')} "
        f"({result.message_count} {_pluralize(result.message_count, 'message')}) "
        f"from {input_path} to {output_path} as {format_name}"
    )
    return 0


def _run_search(input_path: Path, query: str, limit: int) -> int:
    result = search_conversations_sqlite(input_path, query=query, limit=limit)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _run_browse(input_path: Path) -> int:
    conversations = load_conversations_json(input_path)
    run_browse_session(conversations)
    return 0


def _pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"


def _non_empty_string(value: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise argparse.ArgumentTypeError("value must not be empty")
    return normalized_value


def _positive_int(value: str) -> int:
    try:
        integer_value = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc

    if integer_value < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return integer_value


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        return _run_import(args.source, args.input, args.output)

    if args.command == "analyze":
        return _run_analyze(args.input, args.output)

    if args.command == "export":
        return _run_export(args.format, args.input, args.output)

    if args.command == "search":
        return _run_search(args.input, args.query, args.limit)

    if args.command == "browse":
        return _run_browse(args.input)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
