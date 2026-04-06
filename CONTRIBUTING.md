# Contributing to Rica

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone the repo
git clone https://github.com/nexurlabs/rica.git
cd rica

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install dashboard API dependencies
pip install -r dashboard/api/requirements.txt

# Install dashboard web dependencies
cd dashboard/web && npm install && cd ../..

# Run the bot in dev mode
rica start
```

## Project Structure

```
rica/
├── bot/                    # Discord bot (Python)
│   ├── main.py            # Entry point
│   ├── workers/           # Worker modules
│   │   ├── responder.py  # Main chat responder
│   │   ├── moderator.py   # Message moderation
│   │   ├── db_manager.py  # Context management
│   │   └── agent.py       # Autonomous tasks
│   ├── providers/         # LLM provider integrations
│   │   └── factory.py     # Provider factory
│   └── storage/           # Local SQLite storage
│       ├── local_db.py    # SQLite message history
│       └── local_files.py # Local filesystem storage
├── cli/                   # CLI tools
│   ├── main.py            # CLI entry point (rica command)
│   ├── onboard.py         # Interactive setup wizard
│   └── rica_cli.py        # CLI business logic
├── dashboard/
│   ├── api/               # Flask API backend
│   │   ├── main.py        # Flask app entry
│   │   ├── lib.py         # API helpers
│   │   └── routes/        # API endpoints
│   └── web/               # Next.js frontend
│       └── src/app/       # Dashboard pages
├── docs/                  # Documentation (docsify)
└── pyproject.toml         # Python project config
```

## Code Style

- Python: follow PEP 8 — use `ruff` or `black` for formatting
- Type hints required for new Python code
- No `# type: ignore` without a comment explaining why

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature-name`
3. Make your changes
4. Commit with a clear message: `git commit -m "feat: add something"`
5. Push to your fork and open a Pull Request against `main`

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `refactor:` — code change that neither fixes a bug nor adds a feature
- `test:` — adding or updating tests
- `chore:` — maintenance tasks

## Questions?

Open a GitHub Discussion or reach out at `dev@nexurlabs.com`.
