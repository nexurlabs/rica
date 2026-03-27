# Contributing to Rica

Thanks for your interest in contributing to Rica! Here's how to get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/Rishabh20006/rica.git
cd rica

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"

# Run the onboarding wizard
rica onboard

# Start the bot
rica start
```

## Project Structure

- `cli/` — CLI commands and onboarding wizard
- `bot/` — Discord bot runtime, workers, providers, storage
- `dashboard/api/` — FastAPI dashboard backend
- `dashboard/web/` — Next.js dashboard frontend

## Running Tests

```bash
cd bot
python -m pytest tests/ -v
```

## Pull Requests

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the tests
5. Submit a PR

## Code Style

- Python: follow PEP 8
- TypeScript: follow the existing style in `dashboard/web/`
- Use descriptive commit messages

## Issues

Found a bug or have a feature request? [Open an issue](https://github.com/Rishabh20006/rica/issues).
