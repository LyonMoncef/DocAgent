# Project History

## 2026-02-14 — Initial MVP

**Commit:** `57ca501` — feat: initial DocAgent MVP with config query and edit capabilities

### What was built

Personal assistant for querying and editing dotfiles via Claude API.

**Core components:**
- `config_loader.py` — Loads tools.yaml, expands globs, reads config files dynamically
- `llm/base.py` — Abstract LLM interface (for future OpenAI support)
- `llm/claude.py` — Claude API wrapper with tool use support
- `agent.py` — Main orchestrator: detects tools from query, builds context, handles tool calls
- `backup.py` — Versioned backups (keeps last 5) before any edit
- `main.py` — Styled CLI REPL with colored output

**Tools available to Claude:**
- `edit_config` — Replace text in a config file
- `append_to_config` — Add text to end of config file

**Config files tracked:**
- nvim: `~/.config/nvim/init.lua` + `lua/**/*.lua`
- tmux: `~/.tmux.conf` + `~/.config/tmux/tmux.conf`
- zsh: `~/.zshrc`, `~/.p10k.zsh`, `~/.oh-my-zsh/lib/theme-and-appearance.zsh`
- bash: `~/.bashrc`

### Design decisions

1. **Hardcoded tools.yaml** — Start simple, auto-discovery later
2. **Direct context loading** — No vector DB, configs are small enough
3. **Python backend** — User preference, TypeScript for future frontend
4. **Backup policy** — Date-stamped, keep last 5 versions in `backups/` folder

### Known limitations

- Rate limits with large contexts (nvim has 34 lua files)
- No confirmation prompt before edits (trusts Claude's judgment)
- Streaming doesn't work during tool execution (shows after)

---

## 2026-02-14 — UX Improvements

**Commit:** `4685f8a` — feat: add spinner feedback and rate limit retry

- Added animated spinner during loading/waiting states
- Tool executions now highlighted in green
- Rate limit errors auto-retry with exponential backoff (10s, 20s, 40s)
- Reduced zsh config to essential files only (avoid token limits)
- System prompt updated for concise responses

---

## 2026-02-14 — CLI Shortcut

**Commit:** `b3f1276` — feat: add global docagent shell command

- Added `~/.local/bin/docagent` shell script for quick access from anywhere
- Activates venv and runs `src/main.py` automatically
- Supports argument forwarding (`docagent --help`, etc.)
- No need to navigate to project dir or manually activate venv
