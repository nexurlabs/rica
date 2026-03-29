# Rica - Agent Worker
# Separate pipeline for owner + 4 designated users. Code execution + creative tools.

import re
import io
import asyncio
import discord
from sessions import session_manager, build_initial_context
from storage.firestore_client import firestore_client
from providers.factory import get_provider
from prompts import BASE_PROMPTS, DEFAULT_PERSONAS


class AgentWorker:
    """Agent — advanced AI for designated users with code execution + creative tools."""

    async def process(self, message, config: dict) -> str:
        """
        Process an agent message (separate pipeline, bypasses all other workers).
        Returns: response text string (may also send files directly)
        """
        server_id = str(message.guild.id)
        channel_id = str(message.channel.id)

        # Get or create session (30 min timeout, ONE global session per server)
        session, is_new = session_manager.get_or_create(server_id, "agent", channel_id)

        # Load 1000-word context on NEW session only
        initial_context = ""
        if is_new:
            messages = []
            async for msg in message.channel.history(limit=50):
                messages.append(msg)
            initial_context = build_initial_context(messages)

        # Get API key and provider
        w_conf = firestore_client.get_worker_config(server_id, "agent")
        api_key = w_conf["api_key"]
        if not api_key:
            return "⚠️ No API key configured for the Agent. Please set one up in the dashboard."

        provider = get_provider(w_conf["provider"], api_key, model=w_conf["model"])

        # Get system prompt (enforce base prompt + persona)
        base_prompt = BASE_PROMPTS["agent"]
        persona = w_conf["prompt"] or DEFAULT_PERSONAS["agent"]
        prompt = f"{base_prompt}\n\n[SERVER OWNER SYSTEM OVERRIDE / PERSONA]:\n{persona}"

        # Enrich prompt with context
        trigger = config.get("trigger_word", "Rica")
        prompt += f"\n\n[SERVER NAME / TRIGGER WORD]:\nYour visible assistant name in this server is '{trigger}'."

        if initial_context:
            prompt += f"\n\n[RECENT CONTEXT]:\n{initial_context}"

        # Build input
        user_content = self._build_input(message)
        session.add_message("user", user_content)

        # Generate response
        response_text = await provider.generate(
            messages=session.get_history(),
            system_prompt=prompt,
            temperature=0.5,
            max_tokens=4000,
        )

        session.add_message("assistant", response_text)

        # Track usage
        tokens = provider.estimate_tokens(user_content + response_text)
        firestore_client.increment_usage(server_id, "agent", tokens)

        # Check for code execution blocks
        code_blocks = self._extract_code_blocks(response_text)
        if code_blocks:
            for code in code_blocks:
                exec_result = await self._execute_code(code, message, config)
                if exec_result:
                    # Add execution result to session for context
                    session.add_message("user", f"[CODE EXECUTION RESULT]:\n{exec_result}")

            # Clean code blocks from response text
            clean_response = self._clean_response(response_text)
            return clean_response if clean_response.strip() else None

        return response_text

    def _build_input(self, message) -> str:
        """Build input string for agent."""
        user_name = message.author.display_name
        content = message.content

        # Attachments
        attachments = ""
        if message.attachments:
            att_list = [f"{a.filename} ({a.content_type})" for a in message.attachments]
            attachments = f"\n[Attachments: {', '.join(att_list)}]"

        reply_context = ""
        if message.reference and message.reference.resolved:
            ref = message.reference.resolved
            reply_context = f"\n[Replying to {ref.author.display_name}: \"{ref.content[:300]}\"]"

        return f"{user_name}: {content}{reply_context}{attachments}"

    def _extract_code_blocks(self, text: str) -> list:
        """Extract ```execute ... ``` code blocks."""
        pattern = r'```execute\s*\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        return matches

    def _clean_response(self, text: str) -> str:
        """Remove execute code blocks from response text."""
        pattern = r'```execute\s*\n.*?```'
        cleaned = re.sub(pattern, '', text, flags=re.DOTALL)
        return cleaned.strip()

    async def _execute_code(self, code: str, message, config: dict) -> str:
        """Execute Python code in a sandboxed subprocess."""
        from executor import execute_python

        server_id = str(message.guild.id)

        try:
            result = await execute_python(code, server_id, message, config)

            if result.get("error"):
                await message.channel.send(f"```\n❌ Error:\n{result['error'][:1500]}\n```")
                return result["error"]

            output = result.get("output", "")
            if output:
                # Truncate long output
                if len(output) > 1800:
                    output = output[:1800] + "\n... (truncated)"
                await message.channel.send(f"```\n{output}\n```")

            # Handle file outputs (images, audio, video)
            files = result.get("files", [])
            for file_data in files:
                filename = file_data.get("name", "output.bin")
                data = file_data.get("data")
                if data:
                    try:
                        await message.channel.send(
                            file=discord.File(io.BytesIO(data), filename=filename)
                        )
                    except discord.Forbidden:
                        await message.channel.send(
                            f"⚠️ I generated `{filename}`, but I don't have permission to attach files in this channel."
                        )
                        break

            return output or "Code executed successfully."

        except Exception as e:
            error_msg = f"Execution error: {e}"
            await message.channel.send(f"⚠️ {error_msg}")
            firestore_client.log_error(server_id, "agent", error_msg)
            return error_msg


# Global instance
agent_worker = AgentWorker()
