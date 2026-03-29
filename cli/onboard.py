# Rica CLI — Onboarding Wizard
# Interactive step-by-step setup: Discord token → AI provider → API key → Agents → Config

import os
import sys
import asyncio
from pathlib import Path

import yaml
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

# Add bot/ to path for provider imports
_bot_path = os.path.join(os.path.dirname(__file__), "..", "bot")
_bot_path = os.path.abspath(_bot_path)
if _bot_path not in sys.path:
    sys.path.insert(0, _bot_path)

RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
CONFIG_PATH = RICA_HOME / "config.yaml"

PROVIDERS = {
    "1": ("google_ai", "Google AI (Gemini)"),
    "2": ("openai", "OpenAI"),
    "3": ("anthropic", "Anthropic (Claude)"),
    "4": ("openrouter", "OpenRouter"),
    "5": ("groq", "Groq"),
}

WORKERS = {
    "responder": "Responder — AI chat responses to messages",
    "moderator": "Moderator — automatic content moderation",
    "db_manager": "DB Manager — context memory & knowledge base",
    "agent": "Agent — advanced pipeline with code execution (owner only)",
}

console = Console()


def run_onboard():
    """Run the interactive onboarding wizard."""
    from cli.main import VERSION

    # Header
    console.print()
    console.print(Panel.fit(
        "[bold white]Rica — AI Discord Assistant[/bold white]\n"
        f"[dim]v{VERSION} · Open Source · Self-Hosted[/dim]",
        border_style="bright_yellow",
        padding=(1, 4),
    ))
    console.print()

    if CONFIG_PATH.exists():
        overwrite = Confirm.ask(
            f"  [yellow]Config already exists at {CONFIG_PATH}[/yellow]\n"
            "  Overwrite with fresh setup?",
            default=False
        )
        if not overwrite:
            console.print("  [dim]Keeping existing config. Use 'rica start' to run.[/dim]\n")
            return

    config = {}

    # ── Step 1: Discord Bot Token ──────────────────────────────────────
    console.print("[bold]Step 1/4: Discord Bot Token[/bold]")
    console.print("─" * 40)
    console.print("  [dim]Create a bot at https://discord.com/developers/applications[/dim]")
    console.print("  [dim]Copy the token from Bot → Token → Reset Token[/dim]\n")

    while True:
        token = Prompt.ask("  Paste your bot token")
        token = token.strip()

        if not token:
            console.print("  [red]Token cannot be empty.[/red]")
            continue

        # Validate token by calling Discord API
        console.print("  [dim]Validating...[/dim]", end="")
        bot_user = _validate_discord_token(token)
        if bot_user:
            console.print(f"\r  ✅ Token valid — bot: [bold]{bot_user}[/bold]        ")
            config["discord"] = {"token": token}
            break
        else:
            console.print("\r  ❌ Invalid token. Please check and try again.        ")

    console.print()

    # ── Step 2: AI Provider ────────────────────────────────────────────
    console.print("[bold]Step 2/4: AI Provider[/bold]")
    console.print("─" * 40)
    console.print()

    for key, (_, display) in PROVIDERS.items():
        console.print(f"    [{key}] {display}")

    console.print()
    while True:
        choice = Prompt.ask("  Select provider", choices=list(PROVIDERS.keys()), default="1")
        provider_id, provider_name = PROVIDERS[choice]
        break

    console.print(f"  Selected: [bold]{provider_name}[/bold]\n")

    # ── Step 3: API Key ────────────────────────────────────────────────
    console.print("[bold]Step 3/4: API Key[/bold]")
    console.print("─" * 40)
    console.print(f"  [dim]Enter your {provider_name} API key[/dim]\n")

    while True:
        api_key = Prompt.ask("  API key")
        api_key = api_key.strip()

        if not api_key:
            console.print("  [red]API key cannot be empty.[/red]")
            continue

        console.print("  [dim]Validating...[/dim]", end="")
        valid, reason = _validate_api_key(api_key, provider_id)
        if valid:
            console.print(f"\r  ✅ Key valid — provider: [bold]{provider_id}[/bold]        ")
            config["provider"] = {
                "name": provider_id,
                "api_key": api_key,
            }

            # Optional model selection
            console.print()
            console.print("[bold]Step 3.5/4: Model Selection[/bold]")
            console.print("─" * 40)
            console.print("  [dim]Fetching available models for this provider...[/dim]")
            models, model_error = _fetch_provider_models(api_key, provider_id)
            if models:
                for idx, model_name in enumerate(models, start=1):
                    console.print(f"    [{idx}] {model_name}")
                console.print()
                selected = Prompt.ask(
                    "  Select default model",
                    choices=[str(i) for i in range(1, len(models) + 1)],
                    default="1",
                )
                config["provider"]["model"] = models[int(selected) - 1]
                console.print(f"  ✅ Model selected — [bold]{config['provider']['model']}[/bold]")
            else:
                console.print(f"  [yellow]Could not fetch models automatically[/yellow]: {model_error}")
                console.print("  [dim]Continuing without explicit model selection. Provider default will be used.[/dim]")
            break
        else:
            console.print(f"\r  ❌ {reason}        ")

    console.print()

    # ── Step 4: Agent Selection ────────────────────────────────────────
    console.print("[bold]Step 4/4: Agents[/bold]")
    console.print("─" * 40)
    console.print("  [dim]Which agents should be active?[/dim]\n")

    workers_config = {}
    for worker_name, description in WORKERS.items():
        default = worker_name == "responder"  # Responder on by default
        enabled = Confirm.ask(f"    {description}", default=default)
        workers_config[worker_name] = {"enabled": enabled}

    config["workers"] = workers_config
    config["trigger_word"] = "Rica"

    console.print()

    # ── Save Config ─────────────────────────────────────────────────────
    RICA_HOME.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    # Initialize encryption key
    from storage.encryption import encryption
    encryption._get_key()

    # Initialize local database
    from storage.local_db import firestore_client
    existing = firestore_client.get_server_config()
    if not existing:
        firestore_client.create_server_config()

    # Push config into local DB
    _sync_config_to_db(config, firestore_client, encryption)

    # Initialize file storage
    from storage.local_files import gcs_client
    gcs_client.init_server_storage("local")

    # ── Done ────────────────────────────────────────────────────────────
    console.print(Panel.fit(
        "[bold green]✅ Setup Complete![/bold green]\n\n"
        f"  Config saved to [bold]{CONFIG_PATH}[/bold]\n"
        f"  Data directory: [bold]{RICA_HOME}[/bold]\n\n"
        "  [bold]Next steps:[/bold]\n"
        "    • [cyan]rica start[/cyan]      — Launch the bot\n"
        "    • [cyan]rica dashboard[/cyan]  — Open the control panel\n"
        "    • [cyan]rica status[/cyan]     — View your config\n"
        "    • [cyan]rica doctor[/cyan]     — Diagnose issues",
        border_style="green",
        padding=(1, 2),
    ))
    console.print()


def _validate_discord_token(token: str) -> str | None:
    """Validate a Discord bot token. Returns bot username or None."""
    try:
        resp = httpx.get(
            "https://discord.com/api/v10/users/@me",
            headers={"Authorization": f"Bot {token}"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return f"{data['username']}#{data.get('discriminator', '0')}"
        return None
    except Exception:
        return None


def _validate_api_key(api_key: str, provider_id: str) -> tuple[bool, str]:
    """Validate an API key for a provider. Returns (valid, reason)."""
    try:
        from providers.factory import validate_provider_key
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(validate_provider_key(provider_id, api_key))
        loop.close()
        if result:
            return True, "Key validated"
        return False, "Provider authentication failed"
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Validation error: {e}"


def _fetch_provider_models(api_key: str, provider_id: str) -> tuple[list[str], str | None]:
    """Fetch available models for a validated provider key."""
    try:
        from providers.factory import get_provider
        loop = asyncio.new_event_loop()
        provider = get_provider(provider_id, api_key)
        models = loop.run_until_complete(provider.get_models())
        loop.close()
        if not models:
            return [], "No models returned by provider"
        return models, None
    except Exception as e:
        return [], str(e)


def _sync_config_to_db(config: dict, db, encryption):
    """Push config.yaml values into the local database."""
    provider = config.get("provider", {})
    workers = config.get("workers", {})

    updates = {"setup_complete": True}

    if provider.get("name"):
        updates["api_keys.provider"] = provider["name"]

    if provider.get("api_key"):
        updates["api_keys.global_key"] = encryption.encrypt(provider["api_key"])

    if provider.get("model"):
        updates["api_keys.model"] = provider["model"]

    if config.get("trigger_word"):
        updates["trigger_word"] = config["trigger_word"]

    for worker_name, worker_conf in workers.items():
        if isinstance(worker_conf, dict) and "enabled" in worker_conf:
            updates[f"workers.{worker_name}.enabled"] = worker_conf["enabled"]

    db.update_server_config("local", updates)
