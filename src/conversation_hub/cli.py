from __future__ import annotations

import argparse
import json
from pathlib import Path

from conversation_hub.connectors import available_sources
from conversation_hub.pipelines import run_analysis, run_import
from conversation_hub.storage import (
    conversations_to_list,
    load_conversations_json,
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


def _pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        return _run_import(args.source, args.input, args.output)

    if args.command == "analyze":
        return _run_analyze(args.input, args.output)

    if args.command == "export":
        return _run_export(args.format, args.input, args.output)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
