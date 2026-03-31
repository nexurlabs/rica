# Rica - Main Bot Entry Point
# Discord bot with multi-worker pipeline: DB Manager → Moderator → Responder + Agent
# Self-hosted version — uses local SQLite instead of Firestore

import os
import asyncio
import datetime
import discord
from discord.ext import tasks
from config import DISCORD_BOT_TOKEN
from sessions import session_manager, build_initial_context, CONTEXT_WORKERS
from storage.firestore_client import firestore_client
from prompts import DEFAULT_PERSONAS
from rate_limiter import rate_limiter
from errors import safe_error_message


# =============================================================================
# INITIALIZE DISCORD CLIENT
# =============================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True
client = discord.Client(intents=intents)


# =============================================================================
# TRIGGER DETECTION
# =============================================================================
def is_triggered(message: discord.Message, trigger_word: str) -> bool:
    """Check if the message contains the trigger word."""
    content = message.content.lower()
    if trigger_word.lower() in content:
        return True
    if client.user and client.user.mentioned_in(message):
        return True
    return False


# =============================================================================
# GET SERVER CONFIG (local DB — single config for all servers)
# =============================================================================
def get_config(server_id: str) -> dict:
    """Get server config from local DB."""
    config = firestore_client.get_server_config(server_id)
    if not config:
        # Auto-create config if none exists (e.g., first run without onboarding)
        config = firestore_client.create_server_config(server_id)
    return config


def is_worker_enabled(config: dict, worker_name: str, channel_id: str = None) -> bool:
    """Check if a worker is enabled (global or per-channel override)."""
    if not config:
        return False

    # Check per-channel override first
    if channel_id:
        ch_config = firestore_client.get_channel_config(
            config.get("server_id", "local"), str(channel_id)
        )
        if ch_config and "workers" in ch_config:
            ch_worker = ch_config["workers"].get(worker_name)
            if ch_worker is not None:
                return ch_worker.get("enabled", False)

    # Fall back to global config
    return config.get("workers", {}).get(worker_name, {}).get("enabled", False)


def get_worker_prompt(config: dict, worker_name: str) -> str:
    """Get system prompt for a worker (custom or default)."""
    custom = config.get("prompts", {}).get(worker_name, "")
    if custom:
        return custom
    return DEFAULT_PERSONAS.get(worker_name, "")


# =============================================================================
# CONTEXT BUILDER
# =============================================================================
async def fetch_initial_context(channel: discord.TextChannel, limit: int = 50) -> str:
    """Fetch recent messages and build 1000-word context for new sessions."""
    messages = []
    async for msg in channel.history(limit=limit):
        messages.append(msg)
    return build_initial_context(messages)


# =============================================================================
# MESSAGE CHUNKER
# =============================================================================
def chunk_message(text: str, limit: int = 2000) -> list:
    """Split long messages for Discord's 2000 char limit."""
    if len(text) <= limit:
        return [text]

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break

        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()

    return chunks


# =============================================================================
# WORKER PIPELINE
# =============================================================================
async def run_pipeline(message: discord.Message, config: dict):
    """Run the community worker pipeline: DB Manager → Moderator → Responder."""
    server_id = str(message.guild.id)
    channel_id = str(message.channel.id)
    triggered = is_triggered(message, config.get("trigger_word", "Rica"))

    if triggered:
        await message.channel.typing()

    from workers.db_manager import db_manager_worker
    from workers.moderator import moderator_worker
    from workers.responder import responder_worker

    pipeline_context = {
        "db_context": "",
        "mod_context": "",
        "search_results": "",
        "mod_action": None,
    }

    # --- STEP 1: Database Manager ---
    if is_worker_enabled(config, "db_manager", channel_id):
        try:
            db_result = await db_manager_worker.process(message, config)
            pipeline_context["db_context"] = db_result.get("context_for_next", "")
        except Exception as e:
            msg = safe_error_message(e, "db_manager", server_id, firestore_client)
            await message.channel.send(msg)

    # --- STEP 2: Moderator ---
    if is_worker_enabled(config, "moderator", channel_id):
        try:
            mod_result = await moderator_worker.process(message, config, pipeline_context)
            pipeline_context["mod_context"] = mod_result.get("context_for_responder", "")
            pipeline_context["search_results"] = mod_result.get("search_results", "")
            pipeline_context["mod_action"] = mod_result.get("moderation", {})

            mod_action = pipeline_context["mod_action"]
            if mod_action and mod_action.get("action") not in (None, "none"):
                await execute_moderation(message, mod_action)

        except Exception as e:
            msg = safe_error_message(e, "moderator", server_id, firestore_client)
            await message.channel.send(msg)

    # --- STEP 3: Responder (only if triggered) ---
    if triggered and is_worker_enabled(config, "responder", channel_id):
        try:
            response = await responder_worker.process(message, config, pipeline_context)
            if response:
                for chunk in chunk_message(response):
                    await message.reply(chunk, mention_author=False)
        except Exception as e:
            msg = safe_error_message(e, "responder", server_id, firestore_client)
            await message.channel.send(msg)


async def run_agent_pipeline(message: discord.Message, config: dict):
    """Run the Agent pipeline (separate from community pipeline)."""
    server_id = str(message.guild.id)
    await message.channel.typing()

    from workers.agent import agent_worker

    try:
        response = await agent_worker.process(message, config)
        if response:
            for chunk in chunk_message(response):
                await message.reply(chunk, mention_author=False)
    except Exception as e:
        msg = safe_error_message(e, "agent", server_id, firestore_client)
        await message.channel.send(msg)


# =============================================================================
# MODERATION EXECUTOR
# =============================================================================
async def execute_moderation(message: discord.Message, action: dict):
    """Execute a moderation action (warn, delete, mute)."""
    action_type = action.get("action", "none")
    reason = action.get("reason", "No reason provided")
    duration = action.get("duration", 60)

    try:
        if action_type == "warn":
            await message.reply(f"⚠️ Warning: {reason}", mention_author=True)
        elif action_type == "delete":
            await message.delete()
            await message.channel.send(f"🗑️ Message deleted: {reason}")
        elif action_type == "mute":
            if message.guild and message.author:
                await message.author.timeout(
                    discord.utils.utcnow() + datetime.timedelta(seconds=duration),
                    reason=reason
                )
                await message.channel.send(
                    f"🔇 {message.author.display_name} muted for {duration}s: {reason}"
                )
    except discord.Forbidden:
        await message.channel.send("⚠️ I don't have permission to perform that moderation action.")
    except Exception as e:
        print(f"[Moderation] Error: {e}")


# =============================================================================
# BOT COMMANDS
# =============================================================================
async def handle_commands(message: discord.Message, config: dict):
    """Handle bot commands (!status, !usage)."""
    content = message.content.strip().lower()

    if content == "!status":
        workers = config.get("workers", {})
        trigger = config.get("trigger_word", "Rica")

        status_lines = [
            f"**Rica Status** for {message.guild.name}",
            f"Trigger word: `{trigger}`",
            "",
            "**Workers:**",
        ]
        for w_name, w_config in workers.items():
            emoji = "🟢" if w_config.get("enabled") else "🔴"
            status_lines.append(f"{emoji} {w_name.replace('_', ' ').title()}")

        search = config.get("search_config", {})
        s_emoji = "🟢" if search.get("enabled") else "🔴"
        status_lines.append(f"\n{s_emoji} Search (Serper)")

        creative = config.get("creative_config", {})
        for tool_name, tool_conf in creative.items():
            t_emoji = "🟢" if tool_conf.get("enabled") else "🔴"
            status_lines.append(f"{t_emoji} {tool_name.title()}")

        stats = session_manager.get_stats()
        status_lines.append(f"\n**Active Sessions:** {sum(stats.values())}")

        await message.reply("\n".join(status_lines), mention_author=False)
        return True

    elif content == "!usage":
        server_id = str(message.guild.id)
        usage = firestore_client.get_usage_stats(server_id)

        if not usage:
            await message.reply("📊 No usage data yet.", mention_author=False)
            return True

        lines = ["**📊 Usage Stats**", ""]
        for key, value in usage.items():
            if key == "last_updated":
                continue
            label = key.replace("_", " ").title()
            lines.append(f"• {label}: {value:,}")

        await message.reply("\n".join(lines), mention_author=False)
        return True

    return False


# =============================================================================
# EVENTS
# =============================================================================
@client.event
async def on_ready():
    print(f"[Rica] Logged in as {client.user} (ID: {client.user.id})")
    print(f"[Rica] Connected to {len(client.guilds)} servers")
    print(f"[Rica] Mode: Self-hosted (local storage)")

    # Initialize file storage for each connected guild
    from storage.gcs_client import gcs_client
    for guild in client.guilds:
        server_id = str(guild.id)
        gcs_client.init_server_storage(server_id)

    # Restore persisted sessions from local DB
    try:
        session_data = firestore_client.load_sessions()
        if session_data:
            session_manager.import_sessions(session_data)
    except Exception as e:
        print(f"[Rica] Could not restore sessions: {e}")

    if not session_cleanup.is_running():
        session_cleanup.start()


@client.event
async def on_message(message: discord.Message):
    # Ignore DMs and own messages
    if not message.guild or message.author.bot:
        return

    server_id = str(message.guild.id)
    config = get_config(server_id)

    # Auto-derive setup readiness from API key presence
    keys = (config.get("api_keys") or {})
    workers_conf = config.get("workers", {})
    has_any_api_key = any([
        bool(keys.get("global_key")),
        bool(workers_conf.get("db_manager", {}).get("api_key")),
        bool(workers_conf.get("moderator", {}).get("api_key")),
        bool(workers_conf.get("responder", {}).get("api_key")),
        bool(workers_conf.get("agent", {}).get("api_key")),
    ])

    if has_any_api_key and not config.get("setup_complete"):
        firestore_client.update_server_config(server_id, {"setup_complete": True})
        config["setup_complete"] = True

    if not has_any_api_key:
        trigger = config.get("trigger_word", "Rica")
        if is_triggered(message, trigger) or message.content.strip().startswith("!"):
            await message.reply(
                "⚠️ API key not configured yet. Run `rica onboard` to set up your API key.",
                mention_author=False,
            )
        return

    # Handle bot commands
    if message.content.strip().startswith("!"):
        handled = await handle_commands(message, config)
        if handled:
            return

    # --- Rate limiting ---
    user_id = str(message.author.id)
    trigger = config.get("trigger_word", "Rica")
    triggered = is_triggered(message, trigger)

    if triggered or is_worker_enabled(config, "db_manager", str(message.channel.id)) or is_worker_enabled(config, "moderator", str(message.channel.id)):
        allowed, rate_msg = rate_limiter.check(user_id, str(message.channel.id))
        if not allowed:
            if triggered:
                await message.reply(rate_msg, mention_author=False)
            return

    # Check if user is an agent user
    is_agent = firestore_client.is_agent_user(server_id, user_id)

    if is_agent and triggered:
        if is_worker_enabled(config, "agent"):
            await run_agent_pipeline(message, config)
        else:
            await run_pipeline(message, config)
    else:
        await run_pipeline(message, config)


# =============================================================================
# BACKGROUND TASKS
# =============================================================================
@tasks.loop(minutes=5)
async def session_cleanup():
    """Periodically clean up expired sessions and persist active ones."""
    session_manager.clear_expired()
    _save_sessions()


def _save_sessions():
    """Save active sessions to local DB for crash recovery."""
    try:
        data = session_manager.export_sessions()
        firestore_client.save_sessions(data)
    except Exception as e:
        print(f"[Sessions] Failed to persist sessions: {e}")


# =============================================================================
# RUN
# =============================================================================
def main():
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not found! Run 'rica onboard' to set up.")
        return

    print("[Rica] Starting bot...")
    try:
        client.run(DISCORD_BOT_TOKEN)
    finally:
        try:
            import asyncio
            from workers.moderator import moderator_worker
            asyncio.run(moderator_worker.close())
        except Exception:
            pass


if __name__ == "__main__":
    main()
