# Rica - Database Manager Worker
# Reads/writes markdown files via the LocalFileClient, with FTS5 search.
# The LLM is given a `search` tool as the primary way to find context.

import json
from sessions import session_manager
from storage.firestore_client import firestore_client
from storage.gcs_client import gcs_client
from storage.markdown_kb import markdown_kb
from providers.factory import get_provider
from prompts import BASE_PROMPTS, DEFAULT_PERSONAS


# Tool schema surfaced to the LLM in the system prompt. Keeping it explicit
# (not just an English description) so any model can call them reliably.
DB_MANAGER_TOOLS = """\
You can call ONE OR MORE of the following tools per turn. Reply with a
single JSON object: {"thoughts": "...", "context_for_next": "...", "actions": [...]}.

Each action is {"tool": "<name>", "args": {...}}.

  1. search     — args: {"query": "<natural language>", "limit": 5}
                  Returns the top matching markdown snippets with their file
                  paths. PREFER THIS over list_files. Use natural language
                  queries ("server rules for new members", "what does Rish
                  prefer", "previous conversation about chess openings").

  2. read_file  — args: {"path": "knowledge/main.md"}
                  Use this AFTER a search to read the full content of an
                  interesting file. Avoid reading files blindly.

  3. write_file — args: {"path": "<relpath>", "content": "<markdown>"}
                  Overwrites the file. Use for new user profiles, new
                  knowledge entries, or large rewrites.

  4. append_file — args: {"path": "<relpath>", "content": "<markdown>"}
                   Appends to a file. Use for incremental log entries
                   (e.g. appending a dated note to knowledge/main.md or
                   a conversation summary).

  5. list_files — args: {"prefix": "users/"}  (optional)
                  Lists files under a prefix. Use only to discover what
                  exists; prefer search for actually finding content.

  6. list_folders — args: {"prefix": ""}  (optional)
                    Lists top-level folders. Use sparingly.

  7. delete_file — args: {"path": "<relpath>"}
                   Use to remove obsolete entries.

File layout convention (per server):
  knowledge/main.md            — long-running server knowledge base
  users/<user_id>.md           — one file per user with stable schema:
                                   ## Profile
                                   ## Preferences
                                   ## Known facts
                                   ## History
  conversations/<channel_id>/  — episodic memory
  custom/                      — owner-defined structure

In `context_for_next`, summarise what you found and why it matters for
the downstream moderator and responder. Keep it terse — a few sentences
plus the most relevant snippets.
"""


class DBManagerWorker:
    """Database Manager — markdown files + FTS5 search, builds context."""

    async def process(self, message, config: dict) -> dict:
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)

        session, is_new = session_manager.get_or_create(
            server_id, "db_manager", channel_id
        )

        w_conf = firestore_client.get_worker_config(server_id, "db_manager", channel_id)
        api_key = w_conf["api_key"]
        if not api_key:
            return {"context_for_next": ""}

        provider = get_provider(w_conf["provider"], api_key, model=w_conf["model"])

        base_prompt = BASE_PROMPTS["db_manager"]
        persona = w_conf["prompt"] or DEFAULT_PERSONAS["db_manager"]
        prompt = (
            f"{base_prompt}\n\n"
            f"[SERVER OWNER SYSTEM OVERRIDE / PERSONA]:\n{persona}\n\n"
            f"{DB_MANAGER_TOOLS}"
        )

        user_content = self._build_input(message)
        session.add_message("user", user_content)

        response_text = await provider.generate(
            messages=session.get_history(),
            system_prompt=prompt,
            json_mode=True,
            temperature=0.3,
            max_tokens=2000,
        )

        session.add_message("assistant", response_text)
        tokens = provider.estimate_tokens(user_content + response_text)
        firestore_client.increment_usage(server_id, "db_manager", tokens)

        return await self._execute_actions(server_id, response_text)

    def _build_input(self, message) -> str:
        user_name = message.author.display_name
        user_id = str(message.author.id)
        content = message.content
        channel = message.channel.name

        reply_context = ""
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            reply_context = (
                f"\n[Replying to {ref.author.display_name}: "
                f"\"{ref.content[:200]}\"]"
            )

        return (
            f"USER: {user_name} (ID: {user_id})\n"
            f"CHANNEL: #{channel}\n"
            f"MESSAGE: \"{content}\"{reply_context}"
        )

    async def _execute_actions(self, server_id: str, response_text: str) -> dict:
        """Parse LLM response and execute file operations + search."""
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            return {"context_for_next": response_text[:500]}

        actions = result.get("actions", [])
        action_results = []
        search_hits = []

        for action in actions:
            tool = action.get("tool")
            args = action.get("args", {})

            try:
                if tool == "search":
                    query = args.get("query", "")
                    limit = int(args.get("limit", 5))
                    hits = markdown_kb.search(server_id, query, limit=limit)
                    if hits:
                        rendered = "\n".join(
                            f"- {path} (score {score:.2f}): {snip}"
                            for path, snip, score in hits
                        )
                        action_results.append(f"[SEARCH '{query}']:\n{rendered}")
                        search_hits.extend([(p, s) for p, s, _ in hits])
                    else:
                        action_results.append(f"[SEARCH '{query}']: no matches")

                elif tool == "read_file":
                    content = gcs_client.read_file(server_id, args.get("path", ""))
                    snippet = (content or "File not found")[:600]
                    action_results.append(
                        f"[READ {args.get('path')}]: {snippet}"
                    )

                elif tool == "write_file":
                    gcs_client.write_file(
                        server_id,
                        args.get("path", ""),
                        args.get("content", ""),
                    )
                    action_results.append(f"[WRITE {args.get('path')}]: Success")

                elif tool == "append_file":
                    gcs_client.append_file(
                        server_id,
                        args.get("path", ""),
                        args.get("content", ""),
                    )
                    action_results.append(f"[APPEND {args.get('path')}]: Success")

                elif tool == "list_files":
                    files = gcs_client.list_files(
                        server_id, args.get("prefix", "")
                    )
                    file_list = ", ".join(f["path"] for f in files[:20])
                    action_results.append(f"[LIST]: {file_list}")

                elif tool == "list_folders":
                    folders = gcs_client.list_folders(
                        server_id, args.get("prefix", "")
                    )
                    action_results.append(f"[FOLDERS]: {', '.join(folders)}")

                elif tool == "delete_file":
                    gcs_client.delete_file(
                        server_id, args.get("path", "")
                    )
                    action_results.append(
                        f"[DELETE {args.get('path')}]: Success"
                    )

            except Exception as e:
                action_results.append(f"[ERROR {tool}]: {e}")

        context = result.get("context_for_next", "")
        if action_results:
            context += "\n\n[DB Actions]: " + "; ".join(action_results)

        return {
            "context_for_next": context,
            "thoughts": result.get("thoughts", ""),
            "actions_executed": len(actions),
            "search_hits": search_hits,
        }


db_manager_worker = DBManagerWorker()
