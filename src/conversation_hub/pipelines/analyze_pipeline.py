from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from conversation_hub.models.schema import Conversation


_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+|\n+")
_ENTITY_RE = re.compile(r"\b(?:[A-Z][a-z0-9]+|[A-Z]{2,})(?:\s+(?:[A-Z][a-z0-9]+|[A-Z]{2,}))*\b")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "also",
    "can",
    "draft",
    "for",
    "here",
    "how",
    "i",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "or",
    "please",
    "the",
    "to",
    "use",
    "with",
    "you",
    "your",
}
_PROJECT_KEYWORDS = {
    "audit",
    "build",
    "checklist",
    "goal",
    "launch",
    "migration",
    "plan",
    "planning",
    "project",
    "release",
    "roadmap",
    "rollout",
    "ship",
}
_CONSTRAINT_KEYWORDS = {
    "avoid",
    "deterministic",
    "don",
    "don't",
    "keep",
    "must",
    "no",
    "only",
    "prefer",
    "use",
    "without",
}
_ENTITY_BLACKLIST = {
    "bullet",
    "can",
    "draft",
    "here",
    "keep",
    "plan",
    "points",
    "repo",
    "summarize",
    "taildrop repo",
    "use",
}
_ENTITY_PREFIX_BLACKLIST = {"can", "draft", "here", "summarize", "use"}


@dataclass(slots=True)
class AnalysisResult:
    summary: dict[str, Any]
    source_patterns: list[dict[str, Any]]
    recurring_projects_goals: list[dict[str, Any]]
    important_entities: list[dict[str, Any]]
    reusable_prompts: list[dict[str, Any]]
    repeated_preferences_constraints: list[dict[str, Any]]
    unresolved_threads: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": dict(self.summary),
            "source_patterns": [dict(pattern) for pattern in self.source_patterns],
            "recurring_projects_goals": [dict(item) for item in self.recurring_projects_goals],
            "important_entities": [dict(item) for item in self.important_entities],
            "reusable_prompts": [dict(item) for item in self.reusable_prompts],
            "repeated_preferences_constraints": [
                dict(item) for item in self.repeated_preferences_constraints
            ],
            "unresolved_threads": [dict(item) for item in self.unresolved_threads],
        }


def run_analysis(conversations: list[Conversation]) -> AnalysisResult:
    return AnalysisResult(
        summary=_build_summary(conversations),
        source_patterns=_build_source_patterns(conversations),
        recurring_projects_goals=_build_recurring_projects_goals(conversations),
        important_entities=_build_important_entities(conversations),
        reusable_prompts=_build_reusable_prompts(conversations),
        repeated_preferences_constraints=_build_repeated_preferences_constraints(conversations),
        unresolved_threads=_build_unresolved_threads(conversations),
    )


def _build_summary(conversations: list[Conversation]) -> dict[str, Any]:
    source_counts = Counter(conversation.source for conversation in conversations)
    return {
        "conversation_count": len(conversations),
        "message_count": sum(len(conversation.messages) for conversation in conversations),
        "source_counts": {source: source_counts[source] for source in sorted(source_counts)},
    }


def _build_source_patterns(conversations: list[Conversation]) -> list[dict[str, Any]]:
    conversation_counts = Counter(conversation.source for conversation in conversations)
    message_counts = defaultdict(int)
    keyword_counts: dict[str, Counter[str]] = defaultdict(Counter)

    for conversation in conversations:
        message_counts[conversation.source] += len(conversation.messages)
        for text in _iter_source_pattern_texts(conversation):
            keyword_counts[conversation.source].update(_keyword_tokens(text))

    patterns = []
    for source in sorted(conversation_counts):
        top_keywords = [
            keyword
            for keyword, _ in sorted(
                keyword_counts[source].items(),
                key=lambda item: (-item[1], item[0]),
            )[:5]
        ]
        patterns.append(
            {
                "source": source,
                "conversation_count": conversation_counts[source],
                "message_count": message_counts[source],
                "top_keywords": top_keywords,
            }
        )
    return patterns


def _iter_source_pattern_texts(conversation: Conversation) -> list[str]:
    texts: list[str] = []
    if conversation.title:
        texts.append(conversation.title)
    texts.extend(
        _normalize_whitespace(message.text_content)
        for message in conversation.messages
        if message.role == "user" and message.text_content
    )
    return texts


def _keyword_tokens(text: str) -> list[str]:
    return [
        token
        for token in (word.lower() for word in _WORD_RE.findall(text))
        if len(token) > 2 and token not in _STOPWORDS
    ]


def _build_recurring_projects_goals(conversations: list[Conversation]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)

    for conversation in conversations:
        candidate_texts = [conversation.title] if conversation.title else []
        candidate_texts.extend(
            message.text_content for message in conversation.messages if message.role == "user"
        )
        for text in candidate_texts:
            phrase = _project_goal_phrase(text)
            if phrase is None:
                continue
            counts[phrase] += 1
            sources[phrase].add(conversation.source)

    return [
        {
            "count": counts[phrase],
            "phrase": phrase,
            "sources": sorted(sources[phrase]),
        }
        for phrase, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 2
    ]


def _project_goal_phrase(text: str) -> str | None:
    for sentence in _split_sentences(text):
        tokens = [
            token
            for token in (word.lower() for word in _WORD_RE.findall(sentence))
            if token not in _STOPWORDS
        ]
        if len(tokens) < 3:
            continue
        candidate = " ".join(tokens[:3])
        if any(keyword in candidate.split() for keyword in _PROJECT_KEYWORDS):
            return candidate
    return None


def _build_important_entities(conversations: list[Conversation]) -> list[dict[str, Any]]:
    counts: Counter[tuple[str, str]] = Counter()
    display_names: dict[tuple[str, str], str] = {}
    sources: dict[tuple[str, str], set[str]] = defaultdict(set)

    for conversation in conversations:
        for message in conversation.messages:
            text = message.text_content
            if not text:
                continue
            for entity_text in _ENTITY_RE.findall(text):
                entity = _clean_entity_text(entity_text)
                if entity is None:
                    continue
                normalized_entity = entity.lower()
                if normalized_entity in _ENTITY_BLACKLIST:
                    continue
                key = ("name", normalized_entity)
                counts[key] += 1
                display_names.setdefault(key, entity)
                sources[key].add(conversation.source)

    return [
        {
            "count": counts[key],
            "entity": display_names[key],
            "kind": key[0],
            "sources": sorted(sources[key]),
        }
        for key, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], display_names[item[0]].lower()),
        )
        if count >= 2
    ]


def _build_reusable_prompts(conversations: list[Conversation]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)

    for conversation in conversations:
        for message in conversation.messages:
            if message.role != "user":
                continue
            prompt = _normalize_whitespace(message.text_content)
            if len(prompt) < 20:
                continue
            counts[prompt] += 1
            sources[prompt].add(conversation.source)

    return [
        {
            "count": counts[prompt],
            "prompt": prompt,
            "sources": sorted(sources[prompt]),
        }
        for prompt, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 2
    ]


def _build_repeated_preferences_constraints(conversations: list[Conversation]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)

    for conversation in conversations:
        for message in conversation.messages:
            if message.role != "user":
                continue
            for sentence in _split_sentences(message.text_content):
                normalized_sentence = _normalize_sentence(sentence)
                if normalized_sentence is None:
                    continue
                counts[normalized_sentence] += 1
                sources[normalized_sentence].add(conversation.source)

    return [
        {
            "count": counts[text],
            "sources": sorted(sources[text]),
            "text": text,
        }
        for text, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if count >= 2
    ]


def _normalize_sentence(sentence: str) -> str | None:
    normalized = _normalize_whitespace(sentence)
    if not normalized:
        return None
    tokens = [token.lower() for token in _WORD_RE.findall(normalized)]
    if not tokens:
        return None
    if not any(token in _CONSTRAINT_KEYWORDS for token in tokens):
        return None
    return normalized


def _build_unresolved_threads(conversations: list[Conversation]) -> list[dict[str, Any]]:
    unresolved_threads = []

    for conversation in sorted(conversations, key=lambda item: (item.source, item.id)):
        messages = conversation.messages_in_chronological_order()
        if not messages:
            continue
        last_message = messages[-1]
        if last_message.role != "user":
            continue
        unresolved_threads.append(
            {
                "conversation_id": conversation.id,
                "last_message_id": last_message.id,
                "reason": "last_message_from_user",
                "source": conversation.source,
                "title": conversation.title,
                "excerpt": _truncate(_normalize_whitespace(last_message.text_content), limit=120),
            }
        )

    return unresolved_threads


def _split_sentences(text: str) -> list[str]:
    return [segment for segment in _SENTENCE_RE.split(text) if segment.strip()]


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _clean_entity_text(text: str) -> str | None:
    tokens = _normalize_whitespace(text).split()
    while tokens and tokens[0].lower() in _ENTITY_PREFIX_BLACKLIST:
        tokens = tokens[1:]
    if not tokens:
        return None
    return " ".join(tokens)


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."
