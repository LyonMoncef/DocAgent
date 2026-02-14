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

## Scope

| Feature | Status |
|---------|--------|
| Query configs (nvim, tmux, zsh...) | Phase 2 |
| Edit configs with backup | Phase 3 |
| CLI REPL | Phase 4 |
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
python -m src.main
```
