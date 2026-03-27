# Rica - Moderator Worker
# Moderates messages + decides if web search is needed via Serper

import json
import aiohttp
from sessions import session_manager
from storage.firestore_client import firestore_client
from providers.factory import get_provider
from prompts import BASE_PROMPTS, DEFAULT_PERSONAS


class ModeratorWorker:
    """Moderator — reviews messages for violations + decides on web search."""

    def __init__(self):
        self._serper_session = None

    async def _get_http_session(self):
        if self._serper_session is None or self._serper_session.closed:
            self._serper_session = aiohttp.ClientSession()
        return self._serper_session

    async def process(self, message, config: dict, pipeline_context: dict) -> dict:
        """
        Process a message through the Moderator.

        Returns: {
            "moderation": {"action": "none"|"warn"|"delete"|"mute", ...},
            "search_results": "search result text",
            "context_for_responder": "context string"
        }
        """
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # Get or create session (10 min timeout, no history context)
        session, is_new = session_manager.get_or_create(server_id, "moderator", channel_id)

        # 1. Get API Provider and Key
        w_conf = firestore_client.get_worker_config(server_id, "moderator", channel_id)
        api_key = w_conf["api_key"]
        if not api_key:
            return {"moderation": {"action": "none"}, "search_results": "", "context_for_responder": ""}

        provider = get_provider(w_conf["provider"], api_key, model=w_conf["model"])

        # Get system prompt (enforce base prompt + persona)
        base_prompt = BASE_PROMPTS["moderator"]
        persona = w_conf["prompt"] or DEFAULT_PERSONAS["moderator"]
        prompt = f"{base_prompt}\n\n[SERVER OWNER SYSTEM OVERRIDE / PERSONA]:\n{persona}"

        # Build input
        user_content = self._build_input(message, pipeline_context)
        session.add_message("user", user_content)

        # Generate response
        response_text = await provider.generate(
            messages=session.get_history(),
            system_prompt=prompt,
            json_mode=True,
            temperature=0.2,
            max_tokens=800,
        )
        session.add_message("assistant", response_text)

        # Track usage
        tokens = provider.estimate_tokens(user_content + response_text)
        firestore_client.increment_usage(server_id, "moderator", tokens)

        # Parse response
        result = self._parse_response(response_text)

        # Execute search if needed
        search_results = ""
        search_config = config.get("search_config", {})
        if (result.get("search", {}).get("needed")
                and search_config.get("enabled")):
            serper_key = search_config.get("serper_api_key", "")
            if not serper_key:
                # Try to decrypt from Firestore
                full_search = firestore_client.get_search_config(server_id)
                serper_key = full_search.get("serper_api_key", "")

            if serper_key:
                query = result["search"].get("query", "")
                search_results = await self._serper_search(query, serper_key)

        return {
            "moderation": result.get("moderation", {"action": "none"}),
            "search_results": search_results,
            "context_for_responder": result.get("context_for_responder", ""),
        }

    def _build_input(self, message, pipeline_context: dict) -> str:
        """Build input for the Moderator LLM."""
        user_name = message.author.display_name
        user_id = str(message.author.id)
        content = message.content
        channel = message.channel.name

        # Include DB Manager context if available
        db_context = pipeline_context.get("db_context", "")
        db_section = f"\n\n[DB CONTEXT]: {db_context}" if db_context else ""

        # Reply context
        reply_context = ""
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            reply_context = f"\n[Replying to {ref.author.display_name}: \"{ref.content[:200]}\"]"

        return (
            f"USER: {user_name} (ID: {user_id})\n"
            f"CHANNEL: #{channel}\n"
            f"MESSAGE: \"{content}\"{reply_context}{db_section}"
        )

    def _parse_response(self, response_text: str) -> dict:
        """Parse the Moderator's JSON response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "moderation": {"action": "none", "violation_detected": False},
                "search": {"needed": False},
                "context_for_responder": "",
            }

    async def _serper_search(self, query: str, api_key: str, num_results: int = 5) -> str:
        """Perform a web search using Serper API."""
        if not query or not api_key:
            return ""

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": num_results}

        try:
            session = await self._get_http_session()
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []

                    # Organic results
                    for item in data.get("organic", [])[:num_results]:
                        title = item.get("title", "")
                        snippet = item.get("snippet", "")
                        results.append(f"- {title}: {snippet}")

                    # Answer box
                    answer = data.get("answerBox", {})
                    if answer:
                        answer_text = answer.get("answer") or answer.get("snippet", "")
                        if answer_text:
                            results.insert(0, f"[ANSWER]: {answer_text}")

                    search_text = "\n".join(results)
                    print(f"[Moderator] Search for '{query}': {len(results)} results")
                    return search_text
                else:
                    print(f"[Moderator] Search failed: {resp.status}")
                    return ""
        except Exception as e:
            print(f"[Moderator] Search error: {e}")
            return ""


# Global instance
moderator_worker = ModeratorWorker()
