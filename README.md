# DocAgent

Personal assistant for querying and editing your dotfiles/config files using Claude.

## Problem

- "How did I configure X in nvim?" → dig through config files manually
- "What's my tmux prefix?" → open file, search, forget again
- Config knowledge scattered across multiple tools and files

## Solution

- Chat interface that knows your configs
- Ask questions in natural language → get answers from your actual setup
- Edit configs through conversation → automatic backup
- Export structured data for widget generation (no LLM needed)

## Features

| Feature | Status |
|---------|--------|
| Query configs (nvim, tmux, zsh, bash, powertoys) | Done |
| Edit configs with backup | Done |
| CLI REPL with spinner feedback | Done |
| Global `docagent` shell command | Done |
| Manage tracked tools (add/remove/list) | Done |
| List shortcuts (PowerToys) | Done |
| Export widget data (`--export` CLI) | Done |
| Web API / Frontend | Backlog |
| OpenAI support | Backlog |

## Architecture

```
User → CLI → Agent → Claude API
              ↓
        Config Loader (tools.yaml → actual files)
              ↓
        Backup Manager (versioned, last 5)
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

## Usage

```bash
# Interactive REPL (requires API key)
python -m src.main

# Or via global command
docagent

# Export widget data (no API key needed)
python -m src.main --export powertoys -o /tmp/shortcuts.json
```

## Related projects

- [agent-schemas](https://github.com/LyonMoncef/agent-schemas) — JSON Schema contract for inter-agent data exchange
- [WidgetGenerator](https://github.com/LyonMoncef/WidgetGenerator) — Generates Rainmeter skins from exported data
