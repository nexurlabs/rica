# Installation

## Prerequisites

- Python 3.10+
- Discord Bot Token
- LLM API Key (OpenAI / Anthropic / Gemini)
- Git

## Method 1: Quick Install (Recommended)

**One command.**

```bash
curl -fsSL https://raw.githubusercontent.com/nexurlabs/rica/main/install.sh | bash
```

The installer will:
1. Detect your OS and install git, Python, Node.js if missing
2. Clone the repo (or pull if already installed)
3. Create a virtual environment
4. Install all dependencies
5. Launch interactive onboarding — Discord token, API keys, dashboard URL

## Method 2: Manual Install

```bash
# Clone and enter the repo
git clone https://github.com/nexurlabs/rica.git
cd rica

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment file
cp bot/.env.example bot/.env
nano bot/.env  # fill in your keys

# Run
python bot/main.py
```

## Supported Platforms

| Platform | Supported |
|----------|-----------|
| Linux (Ubuntu/Debian) | ✅ Full support |
| macOS | ✅ Full support |
| Windows (PowerShell) | ✅ Full support |
| Raspberry Pi | ✅ Full support |
| FreeBSD | ✅ Full support |

## Verifying the Install

Once Rica is running, you should see:

```
✅ Rica is online!
🌐 Dashboard: http://localhost:3000
📝 Logs: Check the logs directory
```

Invite the bot to your Discord server using the generated invite link.
