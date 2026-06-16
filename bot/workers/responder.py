# Rica - Responder Worker
# Main chat bot — receives context from DB Manager + Moderator + search results

import base64
import mimetypes

from sessions import session_manager, build_initial_context, CONTEXT_WORKERS
from storage.firestore_client import firestore_client
from providers.factory import get_provider
from prompts import BASE_PROMPTS, DEFAULT_PERSONAS

MAX_IMAGE_BYTES = 8 * 1024 * 1024


class ResponderWorker:
    """Responder — the main chatbot that generates replies."""

    async def process(self, message, config: dict, pipeline_context: dict) -> str:
        """
        Process a triggered message and generate a response.

        Returns: response text string
        """
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # Always load fresh channel history so we see ALL recent messages including
        # other bots (trish/agent) and users — not just our own session history.
        # This ensures trish's replies are always visible as context.
        messages = []
        async for msg in message.channel.history(limit=50, before=message):
            messages.append(msg)
        initial_context = build_initial_context(messages)

        # Get or create session (30 min timeout, per-channel)
        session, is_new = session_manager.get_or_create(server_id, "responder", channel_id)
        # Note: channel history loaded above for fresh context every turn

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

        # Build user message. For multimodal models, image blocks are stored
        # in session history too so they replay on subsequent turns.
        user_text = self._build_text_input(message)
        is_multimodal = getattr(provider, "model", "") == "MiniMax-M3"
        image_blocks = (
            await self._build_image_blocks(message) if is_multimodal else []
        )

        if is_multimodal:
            # Build the multimodal content once and reuse it for both the
            # current generation and the history append.
            user_content = [{"type": "text", "text": user_text}, *image_blocks]
            history_user_content = (
                [
                    {"type": "text", "text": self._build_session_input(message, user_text)},
                    *image_blocks,
                ]
                if image_blocks
                else self._build_session_input(message, user_text)
            )
        else:
            user_content = self._build_session_input(message, user_text)
            history_user_content = user_content
        generation_messages = session.get_history() + [
            {"role": "user", "content": user_content}
        ]

        # Generate response
        response_text = await provider.generate(
            messages=generation_messages,
            system_prompt=enriched_prompt,
            temperature=0.7,
            max_tokens=2000,
        )

        session.add_message("user", history_user_content)
        session.add_message("assistant", response_text)

        # Track usage
        tokens = provider.estimate_tokens(user_text + response_text)
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

    def _build_text_input(self, message) -> str:
        """Build the text portion of user input."""
        user_name = message.author.display_name
        content = message.content

        # Reply context
        reply_context = ""
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            ref_text = ref.content or ""
            ref_att_list = [
                f"{a.filename} ({a.content_type or 'unknown type'})"
                for a in (ref.attachments or [])
                if a.content_type or a.filename
            ]
            ref_attach = ""
            if ref_att_list:
                ref_attach = f" [attachments: {', '.join(ref_att_list)}]"
            reply_context = (
                f"\n[Replying to {ref.author.display_name}: \"{ref_text[:200]}\"{ref_attach}]"
            )

        return f"{user_name}: {content}{reply_context}"

    def _build_session_input(self, message, user_text: str) -> str:
        """Build the compact session-history version of user input.

        Includes both the user's own attachments AND any attachments on the
        message being replied to, so visual context is preserved in history
        even when the bytes themselves are dropped.
        """
        att_parts = []
        for a in (message.attachments or []):
            att_parts.append(f"{a.filename} ({a.content_type or 'unknown type'})")
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            for a in (ref.attachments or []):
                att_parts.append(
                    f"[from replied-to {ref.author.display_name}] {a.filename} "
                    f"({a.content_type or 'unknown type'})"
                )
        if not att_parts:
            return user_text
        return f"{user_text}\n[Attachments: {', '.join(att_parts)}]"

    async def _build_generation_input(self, message, user_text: str):
        """Build text + image blocks for multimodal-capable providers."""
        image_blocks = await self._build_image_blocks(message)
        if not image_blocks:
            return user_text
        return [{"type": "text", "text": user_text}, *image_blocks]

    async def _build_image_blocks(self, message) -> list[dict]:
        """Convert Discord image attachments to Anthropic-style image blocks.

        Reads images from BOTH the current message AND the message being
        replied to (if any), so Kiana/Rica can see images other users sent
        that the user is now reacting to.
        """
        blocks: list[dict] = []
        seen_keys: set[str] = set()

        # Collect candidate (attachment, source_label) pairs
        candidates: list[tuple] = []
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            for a in (ref.attachments or []):
                candidates.append((a, f"from replied-to {ref.author.display_name}"))
        for a in (message.attachments or []):
            candidates.append((a, None))

        for attachment, _label in candidates:
            # Dedupe by proxy_url so we don't double-load the same image
            key = getattr(attachment, "proxy_url", None) or attachment.url
            if key in seen_keys:
                continue
            seen_keys.add(key)

            content_type = attachment.content_type or mimetypes.guess_type(
                attachment.filename
            )[0]
            if not content_type or not content_type.startswith("image/"):
                continue
            if attachment.size and attachment.size > MAX_IMAGE_BYTES:
                continue

            try:
                data = await attachment.read(use_cached=True)
            except Exception as e:  # network/CDP hiccup; skip this one
                continue
            if len(data) > MAX_IMAGE_BYTES:
                continue

            blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": content_type,
                    "data": base64.b64encode(data).decode("ascii"),
                },
            })
        return blocks


# Global instance
responder_worker = ResponderWorker()
