# Rica - Responder Worker
# Main chat bot — receives context from DB Manager + Moderator + search results

from sessions import session_manager, build_initial_context, CONTEXT_WORKERS
from storage.firestore_client import firestore_client
from providers.factory import get_provider
from prompts import BASE_PROMPTS, DEFAULT_PERSONAS


class ResponderWorker:
    """Responder — the main chatbot that generates replies."""

    async def process(self, message, config: dict, pipeline_context: dict) -> str:
        """
        Process a triggered message and generate a response.

        Returns: response text string
        """
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # Get or create session (30 min timeout, per-channel)
        session, is_new = session_manager.get_or_create(server_id, "responder", channel_id)

        # Load 1000-word context on NEW session only
        initial_context = ""
        if is_new:
            messages = []
            async for msg in message.channel.history(limit=50):
                messages.append(msg)
            initial_context = build_initial_context(messages)

        # 1. Check if provider is configured and available
        w_conf = firestore_client.get_worker_config(server_id, "responder", channel_id)
        api_key = w_conf["api_key"]
        if not api_key:
            return "⚠️ No API key configured for the Responder. Please set one up in the dashboard."

        provider = get_provider(w_conf["provider"], api_key, model=w_conf["model"])

        # Get system prompt (enforce base prompt + persona)
        base_prompt = BASE_PROMPTS["responder"]
        persona = w_conf["prompt"] or DEFAULT_PERSONAS["responder"]
        prompt = f"{base_prompt}\n\n[SERVER OWNER SYSTEM OVERRIDE / PERSONA]:\n{persona}"

        # Build enriched prompt with context from previous workers
        enriched_prompt = self._build_enriched_prompt(
            prompt, pipeline_context, initial_context, config
        )

        # Build user message
        user_content = self._build_input(message)
        session.add_message("user", user_content)

        # Generate response
        response_text = await provider.generate(
            messages=session.get_history(),
            system_prompt=enriched_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        session.add_message("assistant", response_text)

        # Track usage
        tokens = provider.estimate_tokens(user_content + response_text)
        firestore_client.increment_usage(server_id, "responder", tokens)

        # Clean up trigger word from response if accidentally included
        trigger = config.get("trigger_word", "Rica")
        response_text = response_text.strip()

        return response_text

    def _build_enriched_prompt(self, base_prompt: str, pipeline_context: dict,
                                initial_context: str, config: dict) -> str:
        """Build system prompt enriched with pipeline context."""
        parts = [base_prompt]

        # Initial context (only on new session)
        if initial_context:
            parts.append(f"\n\n[RECENT CONVERSATION CONTEXT (for reference only)]:\n{initial_context}")

        # DB Manager context
        db_context = pipeline_context.get("db_context", "")
        if db_context:
            parts.append(f"\n\n[DATABASE CONTEXT]:\n{db_context}")

        # Moderator context
        mod_context = pipeline_context.get("mod_context", "")
        if mod_context:
            parts.append(f"\n\n[MODERATOR NOTES]:\n{mod_context}")

        # Search results (passed directly from Moderator)
        search_results = pipeline_context.get("search_results", "")
        if search_results:
            parts.append(
                f"\n\n[SEARCH RESULTS (use these to answer factual questions)]:\n{search_results}"
            )

        # Server identity
        trigger = config.get("trigger_word", "Rica")
        parts.append(f"\n\nYour trigger word/name is: {trigger}")

        return "\n".join(parts)

    def _build_input(self, message) -> str:
        """Build user input string."""
        user_name = message.author.display_name
        content = message.content

        # Reply context
        reply_context = ""
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            reply_context = f"\n[Replying to {ref.author.display_name}: \"{ref.content[:200]}\"]"

        return f"{user_name}: {content}{reply_context}"


# Global instance
responder_worker = ResponderWorker()
