from __future__ import annotations

from collections.abc import Callable
from typing import Any

from conversation_hub.models.schema import Conversation
from conversation_hub.pipelines import AnalysisResult, run_analysis


InputFn = Callable[[], str]
OutputFn = Callable[[object], None]


def run_browse_session(
    conversations: list[Conversation],
    input_fn: InputFn | None = None,
    output_fn: OutputFn | None = None,
) -> None:
    input_fn = input if input_fn is None else input_fn
    output_fn = print if output_fn is None else output_fn

    if not conversations:
        output_fn("Conversation browser")
        output_fn("====================")
        output_fn("No conversations loaded.")
        output_fn("Quit browser.")
        return

    while True:
        _render_conversation_list(conversations, output_fn)
        command = _read_command("List command [number, r, q]:", input_fn, output_fn)

        if command == "q":
            output_fn("Quit browser.")
            return

        if command == "r":
            _render_analysis_report("Overall report", run_analysis(conversations), output_fn)
            continue

        conversation_index = _parse_conversation_selection(command, len(conversations))
        if conversation_index is None:
            output_fn(f"Unrecognized command: {command or '(empty)'}")
            continue

        if _run_conversation_session(
            conversation_number=conversation_index + 1,
            conversation=conversations[conversation_index],
            input_fn=input_fn,
            output_fn=output_fn,
        ):
            return


def _run_conversation_session(
    conversation_number: int,
    conversation: Conversation,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> bool:
    while True:
        _render_conversation_details(conversation_number, conversation, output_fn)
        command = _read_command("Conversation command [m, a, b, q]:", input_fn, output_fn)

        if command == "q":
            output_fn("Quit browser.")
            return True

        if command == "b":
            return False

        if command == "m":
            _render_messages(conversation, output_fn)
            continue

        if command == "a":
            _render_analysis_report(
                f"Analysis report for conversation {conversation.id}",
                run_analysis([conversation]),
                output_fn,
            )
            continue

        output_fn(f"Unrecognized command: {command or '(empty)'}")


def _render_conversation_list(conversations: list[Conversation], output_fn: OutputFn) -> None:
    output_fn("Conversation browser")
    output_fn("====================")
    for index, conversation in enumerate(conversations, start=1):
        title = conversation.title or "(untitled)"
        updated_at = _format_timestamp(conversation.updated_at) or "-"
        output_fn(
            f"{index}. {title} | source={conversation.source} | "
            f"messages={len(conversation.messages)} | updated={updated_at}"
        )


def _render_conversation_details(
    conversation_number: int,
    conversation: Conversation,
    output_fn: OutputFn,
) -> None:
    output_fn(f"Conversation {conversation_number}")
    output_fn("================")
    output_fn(f"ID: {conversation.id}")
    output_fn(f"Title: {conversation.title or '(untitled)'}")
    output_fn(f"Source: {conversation.source}")
    output_fn(f"Messages: {len(conversation.messages)}")
    output_fn(f"Participants: {_format_participants(conversation)}")
    output_fn(f"Created: {_format_timestamp(conversation.created_at) or '-'}")
    output_fn(f"Updated: {_format_timestamp(conversation.updated_at) or '-'}")
    output_fn(f"Tags: {_format_tags(conversation.tags)}")


def _render_messages(conversation: Conversation, output_fn: OutputFn) -> None:
    output_fn(f"Messages for {conversation.id}")
    output_fn("====================")
    for index, message in enumerate(conversation.messages_in_chronological_order(), start=1):
        role = message.role or "unknown"
        text = message.text_content or "(no text)"
        output_fn(f"{index}. [{role}] {text}")


def _render_analysis_report(title: str, report: AnalysisResult, output_fn: OutputFn) -> None:
    report_dict = report.to_dict()
    summary = report_dict["summary"]

    output_fn(title)
    output_fn("=" * len(title))
    output_fn(f"Conversations: {summary['conversation_count']}")
    output_fn(f"Messages: {summary['message_count']}")
    output_fn(f"Source counts: {_format_source_counts(summary['source_counts'])}")

    _render_section(
        "Source patterns",
        [
            (
                f"{item['source']}: conversations={item['conversation_count']}, "
                f"messages={item['message_count']}, "
                f"top_keywords={_format_csv(item['top_keywords'])}"
            )
            for item in report_dict["source_patterns"]
        ],
        output_fn,
    )
    _render_section(
        "Recurring projects/goals",
        [
            f"{item['phrase']} (count={item['count']}, sources={_format_csv(item['sources'])})"
            for item in report_dict["recurring_projects_goals"]
        ],
        output_fn,
    )
    _render_section(
        "Important entities",
        [
            f"{item['entity']} [{item['kind']}] (count={item['count']}, sources={_format_csv(item['sources'])})"
            for item in report_dict["important_entities"]
        ],
        output_fn,
    )
    _render_section(
        "Reusable prompts",
        [
            f"{item['prompt']} (count={item['count']}, sources={_format_csv(item['sources'])})"
            for item in report_dict["reusable_prompts"]
        ],
        output_fn,
    )
    _render_section(
        "Repeated preferences/constraints",
        [
            f"{item['text']} (count={item['count']}, sources={_format_csv(item['sources'])})"
            for item in report_dict["repeated_preferences_constraints"]
        ],
        output_fn,
    )
    _render_section(
        "Unresolved threads",
        [
            (
                f"{item['conversation_id']}: {item['reason']} | "
                f"last_message={item['last_message_id']} | excerpt={item['excerpt']}"
            )
            for item in report_dict["unresolved_threads"]
        ],
        output_fn,
    )


def _render_section(title: str, rows: list[str], output_fn: OutputFn) -> None:
    output_fn(title)
    output_fn("-" * len(title))
    if not rows:
        output_fn("(none)")
        return

    for row in rows:
        output_fn(f"- {row}")


def _read_command(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn(prompt)
    return input_fn().strip().lower()


def _parse_conversation_selection(command: str, conversation_count: int) -> int | None:
    if not command.isdigit():
        return None

    conversation_number = int(command)
    if conversation_number < 1 or conversation_number > conversation_count:
        return None

    return conversation_number - 1


def _format_timestamp(value: Any) -> str | None:
    return None if value is None else value.isoformat()


def _format_source_counts(source_counts: dict[str, int]) -> str:
    if not source_counts:
        return "(none)"
    return ", ".join(f"{source}={count}" for source, count in sorted(source_counts.items()))


def _format_csv(items: list[str]) -> str:
    return ", ".join(items) if items else "(none)"


def _format_participants(conversation: Conversation) -> str:
    participant_labels = []
    for participant in conversation.participants:
        label = participant.display_name or participant.role or participant.id or "unknown"
        participant_labels.append(label)
    return _format_csv(participant_labels)


def _format_tags(tags: list[str]) -> str:
    return _format_csv(tags)
