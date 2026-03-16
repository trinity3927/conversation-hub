from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import Any

from conversation_hub.models.schema import Conversation
from conversation_hub.pipelines import AnalysisResult, run_analysis


InputFn = Callable[[], str]
OutputFn = Callable[[object], None]

_PAGE_SIZE = 8
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")
_URL_RE = re.compile(r"https?://\S+")
_FILE_RE = re.compile(r"\b(?:[\w.-]+/)*[\w.-]+\.(?:md|json|jsonl|txt|csv|pdf|png|jpg|jpeg|svg)\b")
_TASK_VERBS = {
    "add",
    "audit",
    "build",
    "capture",
    "check",
    "create",
    "document",
    "draft",
    "fix",
    "note",
    "plan",
    "prefer",
    "review",
    "ship",
    "summarize",
    "update",
    "write",
}
_TASK_BREAKWORDS = {
    "after",
    "and",
    "because",
    "before",
    "but",
    "if",
    "so",
    "then",
    "while",
    "with",
}
_TASK_STOPWORDS = {
    "a",
    "an",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
}


def run_browse_session(
    conversations: list[Conversation],
    input_fn: InputFn | None = None,
    output_fn: OutputFn | None = None,
) -> None:
    input_fn = input if input_fn is None else input_fn
    output_fn = print if output_fn is None else output_fn

    ordered_conversations = _sort_conversations(conversations)
    active_filter: str | None = None
    active_search: str | None = None
    visible_conversations = ordered_conversations
    current_page = 0

    if not ordered_conversations:
        _render_heading("Conversation Browser", output_fn)
        output_fn("Mode: browse list")
        output_fn("Dataset summary: 0 conversations | 0 messages | (none)")
        output_fn("View: showing 0-0 of 0 | page 1/1")
        output_fn("")
        output_fn("No conversations loaded.")
        output_fn("Legend: [number open] [n next] [p prev] [f filter] [/ search] [r report] [q quit]")
        output_fn("Quit browser.")
        return

    while True:
        page_count = _page_count(len(visible_conversations))
        current_page = max(0, min(current_page, page_count - 1))
        page_conversations = _page_items(visible_conversations, current_page)
        _render_conversation_list(
            all_conversations=ordered_conversations,
            visible_conversations=visible_conversations,
            page_conversations=page_conversations,
            current_page=current_page,
            output_fn=output_fn,
            active_filter=active_filter,
            active_search=active_search,
        )
        command = _read_command("List command [number, n, p, f, /, r, q]:", input_fn, output_fn)

        if command == "q":
            output_fn("Quit browser.")
            return

        if command == "n":
            if current_page + 1 < page_count:
                current_page += 1
            continue

        if command == "p":
            if current_page > 0:
                current_page -= 1
            continue

        if command == "r":
            _render_analysis_report(
                "Overall report",
                run_analysis(visible_conversations),
                visible_conversations,
                output_fn,
            )
            continue

        if command == "f":
            active_filter, visible_conversations = _apply_conversation_filter(
                ordered_conversations,
                input_fn=input_fn,
                output_fn=output_fn,
            )
            current_page = 0
            continue

        if command == "/":
            active_search = _apply_search_query(input_fn=input_fn, output_fn=output_fn)
            current_page = 0
            continue

        conversation_index = _parse_conversation_selection(command, len(page_conversations))
        if conversation_index is None:
            output_fn(f"Unrecognized command: {command or '(empty)'}")
            continue

        conversation_position = current_page * _PAGE_SIZE + conversation_index + 1
        if _run_conversation_session(
            conversation_number=conversation_position,
            total_conversations=len(visible_conversations),
            conversation=page_conversations[conversation_index],
            input_fn=input_fn,
            output_fn=output_fn,
        ):
            return


def _run_conversation_session(
    conversation_number: int,
    total_conversations: int,
    conversation: Conversation,
    input_fn: InputFn,
    output_fn: OutputFn,
) -> bool:
    while True:
        _render_conversation_details(
            conversation_number,
            total_conversations,
            conversation,
            output_fn,
        )
        command = _read_command("Conversation command [m, a, t, b, q]:", input_fn, output_fn)

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
                [conversation],
                output_fn,
            )
            continue

        if command == "t":
            _render_conversation_metadata(conversation, output_fn)
            continue

        output_fn(f"Unrecognized command: {command or '(empty)'}")


def _render_conversation_list(
    all_conversations: list[Conversation],
    visible_conversations: list[Conversation],
    page_conversations: list[Conversation],
    current_page: int,
    output_fn: OutputFn,
    active_filter: str | None = None,
    active_search: str | None = None,
) -> None:
    _render_heading("Conversation Browser", output_fn)
    output_fn("Mode: browse list")
    output_fn(f"Dataset summary: {_dataset_summary(all_conversations)}")
    if active_filter:
        output_fn(f"Active filter: {active_filter}")
    if active_search:
        match_count = _search_match_count(visible_conversations, active_search)
        output_fn(f"Active search: {active_search} ({match_count} matches in current filtered view)")

    output_fn("")
    output_fn(_view_summary(len(visible_conversations), current_page))
    output_fn("")

    if not page_conversations:
        output_fn("No conversations available in the current view.")
    else:
        for index, conversation in enumerate(page_conversations, start=1):
            output_fn(f"{index}. {conversation.title or '(untitled)'}")
            output_fn(
                f"   {conversation.source} | {len(conversation.messages)} msgs | "
                f"updated {_format_timestamp(conversation.updated_at) or '-'}"
            )
            output_fn(f"   preview: {_conversation_preview(conversation)}")
            tasks = _conversation_tasks(conversation)
            if tasks:
                output_fn(f"   tasks: {'; '.join(tasks)}")
            artifacts = _conversation_artifacts(conversation)
            if artifacts:
                output_fn(f"   artifacts: {', '.join(artifacts)}")

    output_fn("")
    output_fn("Legend: [number open] [n next] [p prev] [f filter] [/ search] [r report] [q quit]")


def _render_conversation_details(
    conversation_number: int,
    total_conversations: int,
    conversation: Conversation,
    output_fn: OutputFn,
) -> None:
    _render_heading(f"Conversation {conversation_number} of {total_conversations}", output_fn)
    output_fn("Mode: conversation detail")
    output_fn(f"ID: {conversation.id}")
    output_fn(f"Title: {conversation.title or '(untitled)'}")
    output_fn(f"Source: {conversation.source}")
    output_fn(f"Messages: {len(conversation.messages)}")
    output_fn(f"Participants: {_format_participants(conversation)}")
    output_fn(f"Created: {_format_timestamp(conversation.created_at) or '-'}")
    output_fn(f"Updated: {_format_timestamp(conversation.updated_at) or '-'}")
    output_fn(f"Tags: {_format_tags(conversation.tags)}")
    output_fn(f"Preview: {_conversation_preview(conversation)}")
    tasks = _conversation_tasks(conversation)
    if tasks:
        output_fn(f"Likely tasks: {'; '.join(tasks)}")
    artifacts = _conversation_artifacts(conversation)
    if artifacts:
        output_fn(f"Artifacts: {', '.join(artifacts)}")
    output_fn("")
    output_fn("Operators: [m messages] [a report] [t metadata] [b back] [q quit]")


def _render_messages(conversation: Conversation, output_fn: OutputFn) -> None:
    _render_heading(f"Messages for {conversation.id}", output_fn)
    messages = conversation.messages_in_chronological_order()
    if not messages:
        output_fn("(none)")
        return

    for index, message in enumerate(messages, start=1):
        role = message.role or "unknown"
        text = message.text_content or "(no text)"
        output_fn(f"{index}. [{role}] {text}")


def _render_analysis_report(
    title: str,
    report: AnalysisResult,
    conversations: list[Conversation],
    output_fn: OutputFn,
) -> None:
    report_dict = report.to_dict()
    summary = report_dict["summary"]

    _render_heading(title, output_fn)
    _render_section(
        "Quick summary",
        [
            f"Conversations: {summary['conversation_count']}",
            f"Messages: {summary['message_count']}",
            f"Sources: {_format_source_counts(summary['source_counts'])}",
        ],
        output_fn,
    )
    _render_section(
        "Repeated constraints/preferences",
        [item["text"] for item in report_dict["repeated_preferences_constraints"]],
        output_fn,
    )
    _render_section(
        "Likely tasks",
        _task_rows(conversations),
        output_fn,
    )
    _render_section(
        "Unresolved asks",
        [
            (
                f"{item['conversation_id']}: "
                f"{item['excerpt'] or item['reason']}"
            )
            for item in report_dict["unresolved_threads"]
        ],
        output_fn,
    )
    _render_section(
        "Artifacts",
        _artifact_rows(conversations),
        output_fn,
    )
    _render_section(
        "Source comparison",
        [
            (
                f"{item['source']}: conversations={item['conversation_count']}, "
                f"messages={item['message_count']}"
            )
            for item in report_dict["source_patterns"]
        ],
        output_fn,
    )


def _render_section(title: str, rows: list[str], output_fn: OutputFn) -> None:
    output_fn("")
    _render_subheading(title, output_fn)
    if not rows:
        output_fn("(none)")
        return

    for row in rows:
        output_fn(f"- {row}")


def _render_conversation_metadata(conversation: Conversation, output_fn: OutputFn) -> None:
    output_fn("")
    _render_subheading("Conversation metadata", output_fn)
    output_fn(f"Tags: {_format_tags(conversation.tags)}")
    output_fn(f"Metadata: {_format_metadata(conversation.metadata)}")


def _render_heading(title: str, output_fn: OutputFn) -> None:
    output_fn(title)
    output_fn("=" * len(title))


def _render_subheading(title: str, output_fn: OutputFn) -> None:
    output_fn(title)
    output_fn("-" * len(title))


def _read_command(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn(prompt)
    return input_fn().strip().lower()


def _read_text(prompt: str, input_fn: InputFn, output_fn: OutputFn) -> str:
    output_fn(prompt)
    return input_fn().strip()


def _parse_conversation_selection(command: str, conversation_count: int) -> int | None:
    if not command.isdigit():
        return None

    conversation_number = int(command)
    if conversation_number < 1 or conversation_number > conversation_count:
        return None

    return conversation_number - 1


def _apply_conversation_filter(
    conversations: list[Conversation],
    input_fn: InputFn,
    output_fn: OutputFn,
) -> tuple[str | None, list[Conversation]]:
    keyword = _read_text("Enter filter keyword [blank clears]:", input_fn, output_fn)
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        output_fn("Cleared conversation filter.")
        return None, conversations

    filtered_conversations = [
        conversation
        for conversation in conversations
        if _conversation_matches_query(conversation, normalized_keyword)
    ]
    output_fn(
        f"Showing {len(filtered_conversations)} "
        f"{_pluralize(len(filtered_conversations), 'conversation')} after filter."
    )
    return normalized_keyword, filtered_conversations


def _apply_search_query(input_fn: InputFn, output_fn: OutputFn) -> str | None:
    query = _read_text("Enter search query [blank clears]:", input_fn, output_fn)
    normalized_query = query.strip()
    if not normalized_query:
        output_fn("Cleared search query.")
        return None

    return normalized_query


def _conversation_matches_query(conversation: Conversation, query: str) -> bool:
    normalized_query = query.lower()
    haystacks: list[str] = []
    if conversation.title:
        haystacks.append(conversation.title)
    haystacks.append(conversation.source)
    haystacks.extend(conversation.tags)
    haystacks.extend(
        participant.display_name or participant.role or participant.id or ""
        for participant in conversation.participants
    )
    haystacks.extend(message.text_content for message in conversation.messages if message.text_content)
    return any(normalized_query in haystack.lower() for haystack in haystacks)


def _dataset_summary(conversations: list[Conversation]) -> str:
    conversation_count = len(conversations)
    message_count = sum(len(conversation.messages) for conversation in conversations)
    source_counts = Counter(conversation.source for conversation in conversations)
    return (
        f"{conversation_count} {_pluralize(conversation_count, 'conversation')} | "
        f"{message_count} {_pluralize(message_count, 'message')} | "
        f"{_format_source_counts(source_counts)}"
    )


def _view_summary(total_conversations: int, current_page: int) -> str:
    if total_conversations == 0:
        return "View: showing 0-0 of 0 | page 1/1"

    start = current_page * _PAGE_SIZE + 1
    end = min(start + _PAGE_SIZE - 1, total_conversations)
    page_count = _page_count(total_conversations)
    return f"View: showing {start}-{end} of {total_conversations} | page {current_page + 1}/{page_count}"


def _page_count(total_items: int) -> int:
    return max(1, (total_items + _PAGE_SIZE - 1) // _PAGE_SIZE)


def _page_items(conversations: list[Conversation], current_page: int) -> list[Conversation]:
    start = current_page * _PAGE_SIZE
    end = start + _PAGE_SIZE
    return conversations[start:end]


def _sort_conversations(conversations: Iterable[Conversation]) -> list[Conversation]:
    earliest = datetime.min.replace(tzinfo=timezone.utc)
    return sorted(
        conversations,
        key=lambda conversation: (
            conversation.updated_at or conversation.created_at or earliest,
            conversation.title or "",
            conversation.id,
        ),
        reverse=True,
    )


def _format_timestamp(value: Any) -> str | None:
    return None if value is None else value.isoformat()


def _format_source_counts(source_counts: Counter[str] | dict[str, int]) -> str:
    if not source_counts:
        return "(none)"
    return ", ".join(f"{source}={source_counts[source]}" for source in sorted(source_counts))


def _format_participants(conversation: Conversation) -> str:
    participant_labels = []
    for participant in conversation.participants:
        label = participant.display_name or participant.role or participant.id or "unknown"
        participant_labels.append(label)
    return _format_csv(participant_labels)


def _format_csv(items: list[str]) -> str:
    return ", ".join(items) if items else "(none)"


def _format_tags(tags: list[str]) -> str:
    return _format_csv(tags)


def _format_metadata(metadata: dict[str, object]) -> str:
    if not metadata:
        return "(none)"
    return ", ".join(f"{key}={metadata[key]}" for key in sorted(metadata))


def _conversation_preview(conversation: Conversation) -> str:
    for message in conversation.messages_in_chronological_order():
        sentence = _first_sentence(message.text_content)
        if sentence:
            return _shorten(sentence, 88)

    if conversation.title:
        return _shorten(_normalize_whitespace(conversation.title), 88)

    return "(no preview)"


def _conversation_tasks(conversation: Conversation) -> list[str]:
    tasks: list[str] = []
    seen: set[str] = set()
    for message in conversation.messages_in_chronological_order():
        if message.role != "user":
            continue
        task = _message_task(message.text_content)
        if task is None or task in seen:
            continue
        seen.add(task)
        tasks.append(task)
    return tasks


def _message_task(text: str) -> str | None:
    sentence = _first_sentence(text)
    if not sentence:
        return None

    tokens = [match.group(0) for match in _TOKEN_RE.finditer(sentence)]
    if not tokens:
        return None

    verb = tokens[0].lower()
    if verb not in _TASK_VERBS:
        return None

    task_tokens: list[str] = []
    for token in tokens[1:]:
        lower_token = token.lower()
        if lower_token in _TASK_BREAKWORDS:
            break
        if lower_token in _TASK_STOPWORDS:
            continue
        if token[0].isupper():
            continue
        task_tokens.append(lower_token)
        if len(task_tokens) == 3:
            break

    if not task_tokens:
        return verb

    return " ".join([verb, *task_tokens])


def _conversation_artifacts(conversation: Conversation) -> list[str]:
    artifacts: list[str] = []
    seen: set[str] = set()
    for message in conversation.messages_in_chronological_order():
        for artifact in _extract_artifacts(message.text_content):
            if artifact in seen:
                continue
            seen.add(artifact)
            artifacts.append(artifact)
    return artifacts


def _extract_artifacts(text: str) -> list[str]:
    artifacts: list[str] = []
    for pattern in (_FILE_RE, _URL_RE):
        for match in pattern.findall(text):
            artifact = match.rstrip(".,)")
            if artifact not in artifacts:
                artifacts.append(artifact)
    return artifacts


def _first_sentence(text: str) -> str:
    if not text:
        return ""
    sentences = [segment.strip() for segment in _SENTENCE_RE.split(text) if segment.strip()]
    return _normalize_whitespace(sentences[0]) if sentences else ""


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _task_rows(conversations: list[Conversation]) -> list[str]:
    counts: Counter[str] = Counter()
    for conversation in conversations:
        counts.update(_conversation_tasks(conversation))
    return [
        f"{task} (count={counts[task]})"
        for task, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _artifact_rows(conversations: list[Conversation]) -> list[str]:
    counts: Counter[str] = Counter()
    for conversation in conversations:
        counts.update(_conversation_artifacts(conversation))
    return [
        f"{artifact} (count={counts[artifact]})"
        for artifact, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _search_match_count(conversations: list[Conversation], query: str) -> int:
    return sum(1 for conversation in conversations if _conversation_matches_query(conversation, query))


def _pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else f"{singular}s"
