# Development Notes

## Session: 2026-02-15 — WidgetGenerator pipeline

### What was built
Three new repos forming an inter-agent pipeline:

1. **agent-schemas** (`~/MyPersonalProjects/agent-schemas/`) — JSON Schema contract (`widget_data.schema.json`) defining how agents exchange widget data. Supports `shortcut_table`, `key_value_list`, `status_dashboard` types. Local git only, no remote yet.

2. **DocAgent changes** — `_extract_shortcuts_data()` refactored out of `_tool_list_shortcuts`, new `export_widget_data` tool, and `--export TOOL -o FILE` CLI mode (no API key needed). Commit `c32db1d`.

3. **WidgetGenerator** (`~/MyPersonalProjects/WidgetGenerator/`) — Jinja2-based generator: validates JSON against schema, computes layout, renders Rainmeter `.ini` skins. Local git only, no remote yet.

### Pipeline
```
DocAgent --export powertoys → JSON → WidgetGenerator generate → .ini skin
```
`pipeline.sh powertoys` runs both steps end-to-end. No LLM needed.

### Known issues / next fixes
- **@Resources duplication**: `Background.png` and `GlobalVariables.inc` are copied into each skin's `@Resources/`. Should be symlinked or the skin structure should share a single `@Resources` root. The workaround is per the illustro pattern (each config root has its own `@Resources`).
- **Day colors hardcoded in template**: `color0`–`color6` are duplicated inline in every generated `.ini`. Should come from `GlobalVariables.inc` but Rainmeter's `@include` doesn't merge `[Variables]` sections cleanly. Needs investigation.
- **Skin output path**: Generator writes flat `.ini` into the output dir. The `pipeline.sh` handles the `DocAgent_<Tool>` naming convention — this should be formalized.
- **Two-column layout only**: The `shortcut_table` template drops the Module column and uses group headers. The schema still sends 3 columns — the layout calculator strips the group_by column. This works but is implicit.
- **No remote repos** for `agent-schemas` and `WidgetGenerator` yet — create GitHub repos when ready.
- **Template hardcodes 190px width and illustro-specific values** — should pull from `defaults.py` more consistently.

### Design standards established
- **Font**: Trebuchet MS (via `#fontName#` from GlobalVariables.inc)
- **Colors**: Day-of-week dynamic title via `[#color[&measureDayNumber]]`, text `200,200,200,205`
- **Layout**: 190px width, `X=10` left / `X=200` right-aligned, 14px row spacing
- **Background**: `Background.png` with `BackgroundMode=3`, margins `0,50,0,30`
- **Highlighted rows**: Day color + bold (custom shortcuts that differ from defaults)
- **Group headers**: Day color, bold, with separator lines between groups

## Git Friction Points
_For future git tools project_

## Backlog
- OpenAI integration
- Web API (FastAPI)
- Frontend chat UI
- MCP server integration
- Auto-discovery of dotfiles
- Create GitHub repos for agent-schemas and WidgetGenerator
- Symlink or unify @Resources across generated skins
- Add tmux/nvim shortcut export support to DocAgent
- Support `key_value_list` and `status_dashboard` widget types
