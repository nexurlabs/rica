# Rica - Database Manager Worker
# Reads/writes MD files on GCS, builds context for downstream workers

import json
from sessions import session_manager
from storage.firestore_client import firestore_client
from storage.gcs_client import gcs_client
from providers.factory import get_provider
from prompts import BASE_PROMPTS, DEFAULT_PERSONAS


class DBManagerWorker:
    """Database Manager — stores, analyzes, and retrieves data from MD files on GCS."""

    async def process(self, message, config: dict) -> dict:
        """
        Process a message through the DB Manager.
        Returns: {"context_for_next": "relevant context string"}
        """
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)
        user_id = str(message.author.id)

        # Get or create session (10 min timeout, no history context)
        session, is_new = session_manager.get_or_create(server_id, "db_manager", channel_id)

        # 1. Get API Key and Configs
        w_conf = firestore_client.get_worker_config(server_id, "db_manager", channel_id)
        api_key = w_conf["api_key"]
        if not api_key:
            return {"context_for_next": ""}

        provider = get_provider(w_conf["provider"], api_key, model=w_conf["model"])

        # Get system prompt (enforce base prompt + persona)
        base_prompt = BASE_PROMPTS["db_manager"]
        persona = w_conf["prompt"] or DEFAULT_PERSONAS["db_manager"]
        prompt = f"{base_prompt}\n\n[SERVER OWNER SYSTEM OVERRIDE / PERSONA]:\n{persona}"

        # Build message for the LLM
        user_content = self._build_input(message)

        # Add to session history
        session.add_message("user", user_content)

        # Generate response
        response_text = await provider.generate(
            messages=session.get_history(),
            system_prompt=prompt,
            json_mode=True,
            temperature=0.3,
            max_tokens=1500,
        )

        session.add_message("assistant", response_text)

        # Track usage
        tokens = provider.estimate_tokens(user_content + response_text)
        firestore_client.increment_usage(server_id, "db_manager", tokens)

        # Parse and execute file operations
        result = await self._execute_actions(server_id, response_text)
        return result

    def _build_input(self, message) -> str:
        """Build input string for the DB Manager LLM."""
        user_name = message.author.display_name
        user_id = str(message.author.id)
        content = message.content
        channel = message.channel.name

        # Check if it's a reply
        reply_context = ""
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            reply_context = f"\n[Replying to {ref.author.display_name}: \"{ref.content[:200]}\"]"

        return (
            f"USER: {user_name} (ID: {user_id})\n"
            f"CHANNEL: #{channel}\n"
            f"MESSAGE: \"{content}\"{reply_context}"
        )

    async def _execute_actions(self, server_id: str, response_text: str) -> dict:
        """Parse LLM response and execute file operations on GCS."""
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            return {"context_for_next": response_text[:500]}

        actions = result.get("actions", [])
        action_results = []

        for action in actions:
            tool = action.get("tool")
            args = action.get("args", {})

            try:
                if tool == "read_file":
                    content = gcs_client.read_file(server_id, args.get("path", ""))
                    action_results.append(f"[READ {args.get('path')}]: {content or 'File not found'}")

                elif tool == "write_file":
                    gcs_client.write_file(server_id, args.get("path", ""), args.get("content", ""))
                    action_results.append(f"[WRITE {args.get('path')}]: Success")

                elif tool == "append_file":
                    gcs_client.append_file(server_id, args.get("path", ""), args.get("content", ""))
                    action_results.append(f"[APPEND {args.get('path')}]: Success")

                elif tool == "list_files":
                    files = gcs_client.list_files(server_id, args.get("prefix", ""))
                    file_list = ", ".join(f["path"] for f in files[:20])
                    action_results.append(f"[LIST]: {file_list}")

                elif tool == "list_folders":
                    folders = gcs_client.list_folders(server_id, args.get("prefix", ""))
                    action_results.append(f"[FOLDERS]: {', '.join(folders)}")

                elif tool == "delete_file":
                    gcs_client.delete_file(server_id, args.get("path", ""))
                    action_results.append(f"[DELETE {args.get('path')}]: Success")

            except Exception as e:
                action_results.append(f"[ERROR {tool}]: {e}")

        context = result.get("context_for_next", "")
        if action_results:
            context += "\n\n[DB Actions]: " + "; ".join(action_results)

        return {
            "context_for_next": context,
            "thoughts": result.get("thoughts", ""),
            "actions_executed": len(actions),
        }


# Global instance
db_manager_worker = DBManagerWorker()
