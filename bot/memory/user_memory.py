# Rica - User Memory
# Per-user markdown file with a stable schema. Reads return a structured
# representation; writes go through the LocalFileClient (and the FTS5
# index in storage.markdown_kb keeps itself in sync automatically).
#
# File layout:
#   users/<user_id>.md
#
# Schema (stable headers, enforced by the helpers below):
#   # User: <display_name> (ID: <id>)
#   ## Profile             — short factual fields (rewrite in place)
#   ## Preferences         — short factual fields (rewrite in place)
#   ## Known facts         — append-only dated log
#   ## Conversation patterns — short factual fields (rewrite in place)
#
# The Responder calls `build_context_for_responder(user_id)` to get a
# compact "About this user" block for the system prompt, then after
# replying calls `extract_and_store(server_id, user_id, message, reply)`
# which uses a tiny extractor LLM call to decide what to remember.

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from storage.gcs_client import gcs_client
from storage.markdown_kb import markdown_kb


USER_FILE_DIR = "users"
SECTIONS = ("Profile", "Preferences", "Known facts", "Conversation patterns")


# Cap how much we inject into the Responder prompt. The FTS5 index is
# available for deeper retrieval if needed.
MAX_CONTEXT_CHARS = 1200


def _user_path(user_id: str) -> str:
    return f"{USER_FILE_DIR}/{user_id}.md"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_full() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _empty_file(display_name: str, user_id: str) -> str:
    return (
        f"# User: {display_name} (ID: {user_id})\n\n"
        f"## Profile\n_(none yet)_\n\n"
        f"## Preferences\n_(none yet)_\n\n"
        f"## Known facts\n\n"
        f"## Conversation patterns\n_(none yet)_\n"
    )


def ensure_file(server_id: str, user_id: str, display_name: str) -> str:
    """Create the user file if missing. Returns the file path (relative)."""
    path = _user_path(user_id)
    if not gcs_client.file_exists(server_id, path):
        gcs_client.write_file(server_id, path, _empty_file(display_name, user_id))
    return path


def read(server_id: str, user_id: str, display_name: str = "") -> Optional[str]:
    """Read the full user file. Creates it empty if missing."""
    ensure_file(server_id, user_id, display_name)
    return gcs_client.read_file(server_id, _user_path(user_id))


def _section_bounds(content: str, section: str) -> tuple[int, int]:
    """Find the start and end line indices of a `## <section>` section."""
    lines = content.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip() == f"## {section}":
            start = i + 1
            break
    if start is None:
        return (-1, -1)
    end = len(lines)
    for j in range(start, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    return (start, end)


def rewrite_section(
    server_id: str,
    user_id: str,
    display_name: str,
    section: str,
    new_body: str,
) -> None:
    """Replace the body of a `## <section>` section. Creates section if missing."""
    if section not in SECTIONS:
        raise ValueError(f"Unknown section: {section!r}. Use one of {SECTIONS}")
    ensure_file(server_id, user_id, display_name)
    content = gcs_client.read_file(server_id, _user_path(user_id)) or ""
    lines = content.split("\n")
    start, end = _section_bounds(content, section)
    if start == -1:
        # Section missing — append it at the end.
        new_content = content.rstrip() + f"\n\n## {section}\n{new_body.rstrip()}\n"
    else:
        # start points at the line AFTER the `## section` header; we
        # leave the header in place and only replace the body lines.
        new_body_lines = new_body.rstrip().split("\n")
        lines = lines[:start] + new_body_lines + lines[end:]
        new_content = "\n".join(lines).rstrip() + "\n"
    gcs_client.write_file(server_id, _user_path(user_id), new_content)


def append_known_fact(
    server_id: str,
    user_id: str,
    display_name: str,
    fact: str,
) -> None:
    """Append a dated bullet to the `## Known facts` section."""
    if not fact.strip():
        return
    ensure_file(server_id, user_id, display_name)
    content = gcs_client.read_file(server_id, _user_path(user_id)) or ""
    lines = content.split("\n")
    start, end = _section_bounds(content, "Known facts")
    entry = f"- {_now_iso()}: {fact.strip()}"
    if start == -1:
        # Add the section.
        new_content = content.rstrip() + f"\n\n## Known facts\n{entry}\n"
    else:
        # Insert at the top of the section so newest facts come first.
        lines.insert(start, entry)
        new_content = "\n".join(lines).rstrip() + "\n"
    gcs_client.write_file(server_id, _user_path(user_id), new_content)


def build_context_for_responder(
    server_id: str, user_id: str, display_name: str
) -> str:
    """Return a short 'About this user' block for the system prompt.

    Pulls the file content (capped at MAX_CONTEXT_CHARS) and, when longer,
    also queries the FTS5 index for the most relevant snippets to the
    user's display_name so we can surface the most pertinent facts.
    """
    ensure_file(server_id, user_id, display_name)
    content = gcs_client.read_file(server_id, _user_path(user_id)) or ""
    if not content.strip():
        return ""

    # If the file is small, just return it whole.
    if len(content) <= MAX_CONTEXT_CHARS:
        return content.strip()

    # Otherwise: header + the FTS5-retrieved top snippets.
    header_lines = []
    for line in content.split("\n")[:6]:
        header_lines.append(line)
    header = "\n".join(header_lines)

    hits = markdown_kb.search(server_id, display_name, limit=4)
    snippet_lines = [f"- {path}: {snip}" for path, snip, _score in hits]
    return (
        f"{header}\n\n[Relevant past facts]:\n"
        + ("\n".join(snippet_lines) if snippet_lines else "_(no hits)_")
    )


# =============================================================================
# Extraction — what to remember from a (message, reply) pair
# =============================================================================

EXTRACTOR_SYSTEM_PROMPT = """\
You are a memory extractor for a Discord assistant. Given a single user
message and the assistant's reply, decide what (if anything) is worth
remembering about the user for future conversations.

Only remember things that are:
- Stable facts about the user (name, occupation, location, projects)
- Stated preferences ("I like X", "I always use Y")
- Recurring topics or patterns ("Rish often asks about chess")

Do NOT remember:
- One-off questions ("what's the capital of France")
- Transient state ("I'm tired today")
- The assistant's reply content

Reply with a single JSON object, no other text:
{
  "remember": [
    {"section": "Profile" | "Preferences" | "Known facts" | "Conversation patterns",
     "text": "the fact to remember"}
  ]
}

If nothing is worth remembering, return {"remember": []}.
Use short, factual statements. Section "Known facts" entries will be
automatically dated; you don't need to add a date.
"""


async def extract_and_store(
    server_id: str,
    user_id: str,
    display_name: str,
    user_message: str,
    assistant_reply: str,
    *,
    extractor_provider=None,
    extractor_model: str = "",
) -> int:
    """Decide what to remember from a (message, reply) pair and store it.

    Returns the number of memory items stored. Pass `extractor_provider`
    and `extractor_model` to control which LLM does the extraction; if
    omitted, this is a no-op (the caller can do its own bookkeeping).

    Implementation is intentionally lazy: the provider is injected so
    tests can run synchronously without spinning up Discord.
    """
    if extractor_provider is None:
        return 0
    if not user_message.strip():
        return 0

    user_content = (
        f"USER ({display_name}, id={user_id}) said:\n{user_message}\n\n"
        f"ASSISTANT replied:\n{assistant_reply[:600]}"
    )

    try:
        raw = await extractor_provider.generate(
            messages=[{"role": "user", "content": user_content}],
            system_prompt=EXTRACTOR_SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.0,
            max_tokens=400,
        )
    except Exception as e:
        print(f"[UserMemory] extractor failed: {e}")
        return 0

    import json
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.S)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return 0

    items = parsed.get("remember", []) or []
    stored = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        section = item.get("section", "")
        text = (item.get("text") or "").strip()
        if section not in SECTIONS or not text:
            continue
        if section == "Known facts":
            append_known_fact(server_id, user_id, display_name, text)
        else:
            # Merge into the existing section body if it has the
            # '_(none yet)_' placeholder, else append.
            content = gcs_client.read_file(
                server_id, _user_path(user_id)
            ) or ""
            start, end = _section_bounds(content, section)
            current = ""
            if start != -1:
                section_lines = content.split("\n")[start:end]
                current = "\n".join(section_lines).strip()
            if current in ("", "_(none yet)_"):
                new_body = f"- {text}"
            else:
                new_body = f"{current}\n- {text}"
            rewrite_section(
                server_id, user_id, display_name, section, new_body
            )
        stored += 1
    return stored
