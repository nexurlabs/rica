"""Helpers for cleaning model text before it reaches Discord."""

import re


_REASONING_TAGS = ("think", "reasoning")
_TAG_ALT = "|".join(_REASONING_TAGS)


def strip_reasoning(text: str | None) -> str:
    """Remove private reasoning blocks leaked by reasoning-style models."""
    if not text:
        return ""

    cleaned = str(text)

    # Fenced reasoning blocks from models that expose chain-of-thought as markdown.
    cleaned = re.sub(
        r"```(?:think|thinking|reasoning)\b.*?```",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Complete XML-ish blocks, including tags with attributes.
    cleaned = re.sub(
        rf"<(?:{_TAG_ALT})(?:\s[^>]*)?>.*?</(?:{_TAG_ALT})\s*>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Defensive cleanup for partially stripped history like:
    # "private notes...\n</think>\nvisible answer"
    cleaned = re.sub(
        rf"^.*?</(?:{_TAG_ALT})\s*>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # If a provider gives an opening tag without a closing tag, do not publish it.
    cleaned = re.sub(
        rf"<(?:{_TAG_ALT})(?:\s[^>]*)?>.*$",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove any orphan tags left behind.
    cleaned = re.sub(
        rf"</?(?:{_TAG_ALT})(?:\s[^>]*)?>",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    return re.sub(r"\n[ \t]*\n+", "\n", cleaned).strip()
