# Contributing to Rica

Thank you for your interest in contributing! Here's everything you need to know.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/nexurlabs/rica.git
cd rica

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
pip install -r bot/requirements.txt -r dashboard/api/requirements.txt

# Install dashboard web dependencies
cd dashboard/web && npm install && cd ../../

# Run tests
pytest bot/tests/

# Run the bot in dev mode
rica start
```

## Project Structure

```
rica/
├── bot/                    # Discord bot code
│   ├── main.py            # Entry point
│   ├── workers/           # Worker modules (responder, moderator, agent...)
│   ├── providers/         # AI provider integrations
│   ├── storage/           # Local SQLite storage
│   └── creative/          # Imagen, Veo, Lyria integrations
├── cli/                   # CLI tools
│   ├── onboard.py         # Interactive setup wizard
│   └── main.py            # CLI entry point
├── dashboard/
│   ├── api/              # FastAPI backend
│   └── web/              # Next.js frontend
└── pyproject.toml
```

## Code Style

- Python: follow PEP 8 — use `ruff` or `black` for formatting
- Type hints required for new Python code
- No `# type: ignore` without a comment explaining why

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature-name`
3. Make your changes with tests
4. Ensure tests pass: `pytest bot/tests/`
5. Commit with a clear message: `git commit -m "feat: add something"`
6. Push to your fork and open a Pull Request against `main`

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `refactor:` — code change that neither fixes a bug nor adds a feature
- `test:` — adding or updating tests
- `chore:` — maintenance tasks (deps, tooling, CI)

## Questions?

Open a GitHub Discussion or reach out at `dev@nexurlabs.com`.
