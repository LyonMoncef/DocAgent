# History

## Features

| Feature | Files | Commit |
|---------|-------|--------|
| Initial MVP — config query and edit | `src/agent.py`, `src/config_loader.py`, `src/llm/claude.py`, `src/main.py`, `src/backup.py` | [`60164a3`](#2026-02-14-60164a3) |
| Spinner feedback and rate limit retry | `src/main.py`, `src/llm/claude.py` | [`4fbc0bf`](#2026-02-14-4fbc0bf) |
| Global `docagent` shell command | `HISTORY.md` | [`ffea5d9`](#2026-02-14-ffea5d9) |
| Manage tools (add/remove/list configs) | `src/agent.py`, `src/config_loader.py`, `config/tools.yaml` | [`a13ba3b`](#2026-02-14-a13ba3b) |
| List shortcuts tool (PowerToys) | `src/agent.py`, `src/powertoys_defaults.py`, `config/tools.yaml` | [`fc714eb`](#2026-02-15-fc714eb) |
| Export widget data tool + `--export` CLI | `src/agent.py`, `src/main.py` | [`5f02733`](#2026-02-15-5f02733) |

---

## Changelog

### 2026-02-15 `24a346e`
docs: add WidgetGenerator session notes with known issues and design standards
- Added session summary for the WidgetGenerator pipeline build
- Documented known issues: @Resources duplication, hardcoded day colors, output path naming
- Documented design standards: font, colors, layout, background, highlights
- Added backlog items for future work

### 2026-02-15 `5f02733`
feat: add export_widget_data tool and --export CLI mode
- Extracted `_extract_shortcuts_data()` from `_tool_list_shortcuts` for reuse
- New `export_widget_data` tool produces JSON conforming to agent-schemas contract
- Added to TOOLS list, system prompt, and `_execute_tool()` dispatch
- New `--export TOOL -o FILE` argparse mode in `main.py` — runs without LLM
- `_run_export()` validates output is valid JSON before writing

### 2026-02-15 `fc714eb`
feat: add list_shortcuts tool for colored PowerToys hotkey table
- Parses all PowerToys JSON settings files for hotkey fields
- Compares against known defaults in `powertoys_defaults.py` to detect customizations
- Renders ANSI-colored table: cyan modules, green defaults, yellow+star for custom
- Added `_hotkey_to_str()` and `_humanize_action()` helpers
- Added PowerToys tool definition to `config/tools.yaml`

### 2026-02-15 `7eb4d12`
chore: update powertoys paths to new dotfiles location
- Updated PowerToys config paths in `tools.yaml` to point to new dotfiles repo location

### 2026-02-14 `a13ba3b`
feat: add manage_tools capability to add/remove/list tracked configs
- New `manage_tools` tool with add/remove/list actions
- `ConfigLoader.add_tool()` and `remove_tool()` modify `tools.yaml` with backup
- `ConfigLoader.reload()` re-reads tools config after changes
- PowerToys added as first managed tool

### 2026-02-14 `ffea5d9`
feat: add global docagent shell command
- Added `~/.local/bin/docagent` shell script for quick CLI access
- Activates venv and runs `src/main.py` automatically
- Supports argument forwarding

### 2026-02-14 `4fbc0bf`
feat: add spinner feedback and rate limit retry
- Animated spinner during loading/waiting states in `main.py`
- Tool executions highlighted in green
- Rate limit errors auto-retry with exponential backoff in `claude.py`
- Reduced zsh config to essential files only to avoid token limits

### 2026-02-14 `f569194`
docs: add project history timeline
- Created initial HISTORY.md

### 2026-02-14 `60164a3`
feat: initial DocAgent MVP with config query and edit capabilities
- `config_loader.py` — loads tools.yaml, expands globs, reads config files
- `llm/base.py` — abstract LLM interface for future multi-provider support
- `llm/claude.py` — Claude API wrapper with tool use support
- `agent.py` — orchestrator: detects tools from query, builds context, handles tool calls
- `backup.py` — versioned backups (keeps last 5) before any edit
- `main.py` — styled CLI REPL with colored output
- Tools: `edit_config` (replace text) and `append_to_config` (add to end)
- Tracked configs: nvim, tmux, zsh, bash
