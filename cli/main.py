# Rica CLI — Main Entry Point
# Subcommands: onboard, start, dashboard, status, doctor

import sys
import os
import subprocess
import click
import httpx
from pathlib import Path

# Rica version
VERSION = "0.1.0"

# Add bot/ to path so storage/providers/etc. are importable
_bot_path = os.path.join(os.path.dirname(__file__), "..", "bot")
_bot_path = os.path.abspath(_bot_path)
if _bot_path not in sys.path:
    sys.path.insert(0, _bot_path)

RICA_HOME = Path(os.environ.get("RICA_HOME", Path.home() / ".rica"))
CONFIG_PATH = RICA_HOME / "config.yaml"


def _check_for_updates():
    """Check GitHub for the latest version and print a warning if outdated."""
    try:
        url = "https://raw.githubusercontent.com/nexurlabs/rica/main/pyproject.toml"
        resp = httpx.get(url, timeout=3.0)
        if resp.status_code == 200:
            import re
            match = re.search(r'version\s*=\s*"([^"]+)"', resp.text)
            if match:
                latest_version = match.group(1)
                if latest_version != VERSION:
                    click.echo(f"✨ [Update Available] You are running v{VERSION}, but v{latest_version} is out!")
                    click.echo("   Run 'rica update' to upgrade.\n")
    except Exception:
        pass


@click.group()
@click.version_option(version=VERSION, prog_name="Rica")
def main():
    """Rica — Open-source AI assistant for Discord."""
    pass


@main.command()
def onboard():
    """Interactive setup wizard — configure your bot step by step."""
    from cli.onboard import run_onboard
    run_onboard()


@main.command()
@click.option("--no-dashboard", is_flag=True, help="Start bot only, skip dashboard API")
@click.option("--with-frontend", is_flag=True, help="Also start the dashboard frontend dev server on port 3000")
def start(no_dashboard, with_frontend):
    """Start the Rica bot (and dashboard API)."""
    
    _check_for_updates()
    
    if not CONFIG_PATH.exists():
        click.echo("❌ No config found. Run 'rica onboard' first.")
        sys.exit(1)

    import yaml
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    token = config.get("discord", {}).get("token")
    if not token:
        click.echo("❌ No Discord token in config. Run 'rica onboard' to set it up.")
        sys.exit(1)

    # Initialize local storage with config
    _init_from_config(config)

    if not no_dashboard:
        # Start dashboard API in background thread
        import threading
        dashboard_thread = threading.Thread(target=_start_dashboard, daemon=True)
        dashboard_thread.start()
        click.echo("🌐 Dashboard API running at: http://localhost:8000")

    frontend_url = "http://localhost:3000"
    if with_frontend:
        _start_dashboard_frontend()
        click.echo(f"🖥️  Dashboard UI starting at: {frontend_url}")
    elif not no_dashboard:
        click.echo(f"🖥️  Dashboard UI: {frontend_url}")
        click.echo("   If the page does not load yet, start it in another terminal:")
        click.echo("   cd ~/.nexurlabs/rica/dashboard/web && npm run dev")

    # Start the bot
    click.echo("🤖 Starting Rica bot...")
    os.environ["DISCORD_BOT_TOKEN"] = token
    from bot.main import main as run_bot
    run_bot()


@main.command()
def dashboard():
    """Open the dashboard in your browser."""
    import webbrowser

    if not CONFIG_PATH.exists():
        click.echo("❌ No config found. Run 'rica onboard' first.")
        sys.exit(1)

    dashboard_url = "http://localhost:3000"
    click.echo(f"🌐 Opening dashboard at {dashboard_url}")
    webbrowser.open(dashboard_url)


@main.command()
def status():
    """Show current configuration summary."""
    if not CONFIG_PATH.exists():
        click.echo("❌ No config found. Run 'rica onboard' first.")
        return

    _check_for_updates()

    import yaml
    from rich.console import Console
    from rich.table import Table

    console = Console()

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    console.print("\n[bold]Rica Status[/bold]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value")

    table.add_row("Config", str(CONFIG_PATH))
    table.add_row("Data", str(RICA_HOME))

    discord = config.get("discord", {})
    token = discord.get("token", "")
    table.add_row("Discord Token", f"{'•' * 8}{token[-4:]}" if token else "❌ Not set")

    provider = config.get("provider", {})
    table.add_row("AI Provider", provider.get("name", "not set"))

    api_key = provider.get("api_key", "")
    table.add_row("API Key", f"{'•' * 8}{api_key[-4:]}" if api_key else "❌ Not set")
    table.add_row("Model", provider.get("model", "provider default"))

    trigger = config.get("trigger_word", "Rica")
    table.add_row("Trigger Word", trigger)

    console.print(table)

    # Workers
    console.print("\n[bold]Workers[/bold]")
    workers = config.get("workers", {})
    for name, conf in workers.items():
        emoji = "🟢" if conf.get("enabled") else "🔴"
        console.print(f"  {emoji} {name.replace('_', ' ').title()}")

    console.print()


@main.command()
def doctor():
    """Diagnose common issues."""
    from rich.console import Console
    console = Console()

    console.print("\n[bold]Rica Doctor[/bold]\n")
    issues = 0

    # Check config exists
    if CONFIG_PATH.exists():
        console.print("  ✅ Config file found")
    else:
        console.print("  ❌ Config file missing — run 'rica onboard'")
        issues += 1
        console.print(f"\n  {'⚠️' if issues else '✅'} {issues} issue(s) found.\n")
        return

    # Check config contents
    import yaml
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    # Discord token
    token = config.get("discord", {}).get("token", "")
    if token:
        console.print("  ✅ Discord token configured")
    else:
        console.print("  ❌ Discord token missing")
        issues += 1

    # AI provider
    provider = config.get("provider", {})
    if provider.get("api_key"):
        console.print(f"  ✅ API key configured ({provider.get('name', 'unknown')})")
    else:
        console.print("  ❌ API key missing")
        issues += 1

    # Encryption key
    from storage.encryption import KEY_PATH
    if KEY_PATH.exists():
        console.print("  ✅ Encryption key found")
    else:
        console.print("  ⚠️  Encryption key missing (will be auto-generated on first run)")

    # Database
    from storage.local_db import DB_PATH
    if DB_PATH.exists():
        console.print("  ✅ Database found")
    else:
        console.print("  ⚠️  Database not initialized (will be created on first run)")

    console.print(f"\n  {'⚠️' if issues else '✅'} {issues} issue(s) found.\n")


@main.command()
def update():
    """Update Rica to the latest version."""
    from rich.console import Console
    console = Console()
    
    install_dir = Path(__file__).resolve().parent.parent
    if not (install_dir / ".git").exists():
        console.print("❌ Rica does not appear to be a git repository. Cannot auto-update.")
        return

    console.print("\n[bold]Updating Rica...[/bold]\n")
    try:
        console.print("  [dim]Pulling latest changes...[/dim]")
        subprocess.run(
            ["git", "pull", "--ff-only"], 
            cwd=str(install_dir), 
            check=True,
            capture_output=True,
            text=True
        )
        console.print("  ✅ Pulled latest code")

        console.print("  [dim]Updating dependencies...[/dim]")
        pip_cmd = sys.executable
        subprocess.run(
            [pip_cmd, "-m", "pip", "install", "-r", "bot/requirements.txt", "-r", "dashboard/api/requirements.txt"],
            cwd=str(install_dir),
            check=True,
            capture_output=True,
            text=True
        )
        
        web_dir = install_dir / "dashboard" / "web"
        if web_dir.exists():
            console.print("  [dim]Updating web dependencies...[/dim]")
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            subprocess.run(
                [npm_cmd, "install", "--no-fund", "--no-audit", "--loglevel=error"],
                cwd=str(web_dir),
                check=True,
                capture_output=True,
                text=True
            )
        
        console.print("\n  🎉 [bold green]Rica updated successfully![/bold green]\n")
    except subprocess.CalledProcessError as e:
        console.print(f"\n  ❌ [bold red]Update failed![/bold red]")
        if e.stderr:
            console.print(f"  [red]{e.stderr.strip()}[/red]")
        sys.exit(1)


@main.command()
def stop():
    """Stop any running Rica processes."""
    from rich.console import Console
    import psutil
    console = Console()
    
    console.print("\n[bold]Stopping Rica processes...[/bold]\n")
    
    killed = 0
    current_pid = os.getpid()
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip ourselves
            if proc.info['pid'] == current_pid:
                continue
                
            cmdline = proc.info.get('cmdline') or []
            cmd_str = ' '.join(cmdline).lower()
            
            is_rica = 'rica start' in cmd_str
            is_next = 'next dev' in cmd_str and 'dashboard' in cmd_str
            
            if is_rica or is_next:
                proc.terminate()
                killed += 1
                console.print(f"  🛑 Stopped process {proc.info['pid']} ({proc.info['name']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    if killed > 0:
        console.print(f"\n  ✅ Stopped {killed} processes.\n")
    else:
        console.print("  ℹ️  No running Rica processes found.\n")


def _init_from_config(config: dict):
    """Initialize local storage from config.yaml values."""
    from storage.local_db import firestore_client
    from storage.encryption import encryption

    # Ensure encryption key exists
    encryption._get_key()

    # Get or create server config in SQLite
    existing = firestore_client.get_server_config()
    if not existing:
        firestore_client.create_server_config()

    # Push config.yaml values into local DB
    provider_conf = config.get("provider", {})
    workers_conf = config.get("workers", {})

    updates = {}

    # Set provider
    if provider_conf.get("name"):
        updates["api_keys.provider"] = provider_conf["name"]

    # Set global API key (encrypt it)
    if provider_conf.get("api_key"):
        encrypted_key = encryption.encrypt(provider_conf["api_key"])
        updates["api_keys.global_key"] = encrypted_key

    # Set default model
    if provider_conf.get("model"):
        updates["api_keys.model"] = provider_conf["model"]

    # Set trigger word
    if config.get("trigger_word"):
        updates["trigger_word"] = config["trigger_word"]

    # Set worker enabled states
    for worker_name, worker_conf in workers_conf.items():
        if isinstance(worker_conf, dict):
            if "enabled" in worker_conf:
                updates[f"workers.{worker_name}.enabled"] = worker_conf["enabled"]

    if updates:
        firestore_client.update_server_config("local", updates)
        updates_with_setup = {"setup_complete": True}
        firestore_client.update_server_config("local", updates_with_setup)


def _start_dashboard():
    """Start the dashboard API server in a thread."""
    import uvicorn
    # Add dashboard api path
    api_path = os.path.join(os.path.dirname(__file__), "..", "dashboard", "api")
    api_path = os.path.abspath(api_path)
    if api_path not in sys.path:
        sys.path.insert(0, api_path)

    os.environ.setdefault("JWT_SECRET", "rica-local-dashboard-" + os.urandom(16).hex())

    from dashboard.api.main import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


def _start_dashboard_frontend():
    """Start the Next.js dashboard frontend in the background."""
    web_dir = Path(__file__).resolve().parent.parent / "dashboard" / "web"
    if not web_dir.exists():
        click.echo("⚠️  Dashboard web folder not found; skipping frontend startup.")
        return

    try:
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(web_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except FileNotFoundError:
        click.echo("⚠️  npm not found; cannot auto-start dashboard frontend.")


if __name__ == "__main__":
    main()
