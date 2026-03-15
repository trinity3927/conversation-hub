from __future__ import annotations

import argparse
import json
from pathlib import Path

from conversation_hub.connectors import ClaudeExportConnector, Connector, ChatGPTExportConnector
from conversation_hub.storage import conversations_to_list


CONNECTOR_REGISTRY: dict[str, type[Connector]] = {
    ChatGPTExportConnector.source_name: ChatGPTExportConnector,
    ClaudeExportConnector.source_name: ClaudeExportConnector,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="conversation-hub")
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser("import", help="Import a conversation export into normalized JSON")
    import_parser.add_argument(
        "--source",
        required=True,
        choices=sorted(CONNECTOR_REGISTRY),
        help="Connector source to use for the input export",
    )
    import_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to the source export file",
    )
    import_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the normalized JSON file",
    )

    return parser


def _run_import(source: str, input_path: Path, output_path: Path) -> int:
    connector_class = CONNECTOR_REGISTRY[source]
    conversations = list(connector_class(input_path).fetch())
    payload = conversations_to_list(conversations)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    message_count = sum(len(conversation.messages) for conversation in conversations)
    print(
        f"Imported {len(conversations)} {_pluralize(len(conversations), 'conversation')} "
        f"({message_count} {_pluralize(message_count, 'message')}) from {source} to {output_path}"
    )
    return 0


def _pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import":
        return _run_import(args.source, args.input, args.output)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
