import os
import re
from typing import Optional

from .backup import BackupManager
from .config_loader import ConfigLoader
from .llm.base import BaseLLM


SYSTEM_PROMPT = """You are DocAgent, a concise assistant for dotfiles/config management.

RULES:
- Be brief. Max 5-10 lines unless user asks for details.
- When user asks to CHANGE something, use edit_config or append_to_config tool immediately.
- IMPORTANT: Use the exact file paths from <config_files>. Never use example paths like /home/user/.
- If multiple approaches exist, pick the best one. Don't list alternatives.
- You can add/remove/list managed tools via the manage_tools tool. Use it when the user wants to track a new config or stop tracking one.

Available config files: {tools}
"""

# Tool definitions for Claude
TOOLS = [
    {
        "name": "edit_config",
        "description": "Edit a configuration file by replacing text. Use this when the user asks to change/modify/update a config.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the config file (e.g., /home/user/.zshrc)"
                },
                "old_text": {
                    "type": "string",
                    "description": "The exact text to find and replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "The new text to insert"
                }
            },
            "required": ["file_path", "old_text", "new_text"]
        }
    },
    {
        "name": "append_to_config",
        "description": "Append text to the end of a configuration file. Use when adding new config that doesn't replace existing content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the config file"
                },
                "text": {
                    "type": "string",
                    "description": "The text to append"
                }
            },
            "required": ["file_path", "text"]
        }
    },
    {
        "name": "manage_tools",
        "description": "Add, remove, or list managed configuration tools. Use when the user wants to track a new config (e.g., 'add my kitty config') or stop tracking one.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["add", "remove", "list"],
                    "description": "The action to perform"
                },
                "key": {
                    "type": "string",
                    "description": "Tool key identifier (e.g., 'kitty'). Required for add/remove."
                },
                "name": {
                    "type": "string",
                    "description": "Display name (e.g., 'Kitty'). Required for add."
                },
                "description": {
                    "type": "string",
                    "description": "Tool description (e.g., 'Kitty terminal emulator'). Required for add."
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of config file paths or globs (e.g., ['~/.config/kitty/kitty.conf']). Required for add."
                }
            },
            "required": ["action"]
        }
    }
]


class DocAgent:
    def __init__(
        self,
        llm: BaseLLM,
        config_loader: Optional[ConfigLoader] = None,
        backup_manager: Optional[BackupManager] = None,
    ):
        self.llm = llm
        self.config_loader = config_loader or ConfigLoader()
        self.backup_manager = backup_manager or BackupManager()
        self.messages: list[dict] = []
        self.current_context: str = ""

    def _detect_tools(self, query: str) -> list[str]:
        """
        Detect which tools are mentioned in the query.
        Returns list of tool names to load.
        """
        query_lower = query.lower()
        detected = []

        for tool_name in self.config_loader.list_tools():
            tool_info = self.config_loader.get_tool_info(tool_name)
            if not tool_info:
                continue

            # Check tool key, name, and common variations
            name = tool_info.get("name", "").lower()
            if (
                tool_name in query_lower
                or name in query_lower
            ):
                detected.append(tool_name)

        # Check aliases - maps keywords to tool names
        aliases = {
            "vim": "nvim",
            "neovim": "nvim",
            "editor": "nvim",
            "shell": "zsh",
            "terminal": "tmux",
            "mux": "tmux",
            "window": "tmux",
            "pane": "tmux",
            "session": "tmux",
        }
        for alias, tool_name in aliases.items():
            if alias in query_lower and tool_name not in detected:
                detected.append(tool_name)

        # Shell-specific keywords that should load zsh AND bash
        shell_keywords = ["ls ", "ls_colors", "dircolors", "alias", "export", "path", "prompt", "color"]
        if any(kw in query_lower for kw in shell_keywords):
            if "zsh" not in detected:
                detected.append("zsh")
            if "bash" not in detected:
                detected.append("bash")

        # If no specific tool detected, check for general config keywords
        if not detected:
            general_keywords = ["config", "setting", "keybind", "keymap", "shortcut", "plugin", "theme", "change", "modify", "edit"]
            if any(kw in query_lower for kw in general_keywords):
                # Load all tools for general queries
                detected = self.config_loader.list_tools()

        return detected

    def _build_system_prompt(self, tool_names: list[str]) -> str:
        """Build system prompt with available tools listed."""
        tools_str = ", ".join(tool_names) if tool_names else "none loaded"
        return SYSTEM_PROMPT.format(tools=tools_str)

    def _execute_tool(self, name: str, inputs: dict) -> str:
        """Execute a tool and return the result."""
        if name == "edit_config":
            return self._tool_edit_config(
                inputs["file_path"],
                inputs["old_text"],
                inputs["new_text"]
            )
        elif name == "append_to_config":
            return self._tool_append_config(
                inputs["file_path"],
                inputs["text"]
            )
        elif name == "manage_tools":
            return self._tool_manage_tools(inputs)
        else:
            return f"Unknown tool: {name}"

    def _tool_manage_tools(self, inputs: dict) -> str:
        """Add, remove, or list managed tools."""
        action = inputs["action"]

        if action == "list":
            tools = self.config_loader.list_tools()
            if not tools:
                return "No tools configured."
            lines = []
            for key in tools:
                info = self.config_loader.get_tool_info(key)
                name = info.get("name", key) if info else key
                paths = info.get("paths", []) if info else []
                lines.append(f"- {key}: {name} ({', '.join(paths)})")
            return "Managed tools:\n" + "\n".join(lines)

        if action == "add":
            for field in ("key", "name", "description", "paths"):
                if field not in inputs or not inputs[field]:
                    return f"Error: '{field}' is required for add."
            return self.config_loader.add_tool(
                inputs["key"], inputs["name"], inputs["description"], inputs["paths"]
            )

        if action == "remove":
            if "key" not in inputs or not inputs["key"]:
                return "Error: 'key' is required for remove."
            return self.config_loader.remove_tool(inputs["key"])

        return f"Unknown action: {action}"

    def _tool_edit_config(self, file_path: str, old_text: str, new_text: str) -> str:
        """Edit a config file by replacing text."""
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"

        with open(file_path, "r") as f:
            content = f.read()

        if old_text not in content:
            return f"Error: Text not found in {file_path}. Make sure old_text matches exactly."

        # Backup before editing
        backup_path = self.backup_manager.backup(file_path)

        # Apply edit
        new_content = content.replace(old_text, new_text, 1)
        with open(file_path, "w") as f:
            f.write(new_content)

        return f"Success: Edited {file_path}. Backup saved to {backup_path}"

    def _tool_append_config(self, file_path: str, text: str) -> str:
        """Append text to a config file."""
        file_path = os.path.expanduser(file_path)

        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"

        # Backup before editing
        backup_path = self.backup_manager.backup(file_path)

        # Append
        with open(file_path, "a") as f:
            f.write("\n" + text + "\n")

        return f"Success: Appended to {file_path}. Backup saved to {backup_path}"

    def query(self, user_input: str, stream: bool = False):
        """
        Process a user query and return the response.
        Handles tool calls automatically.
        """
        # Detect which tools to load
        detected_tools = self._detect_tools(user_input)

        # Build context from config files
        if detected_tools:
            self.current_context = self.config_loader.build_context(detected_tools)
        else:
            self.current_context = ""

        # Build the user message with context
        if self.current_context:
            context_message = f"""<config_files>
{self.current_context}
</config_files>

User question: {user_input}"""
        else:
            context_message = user_input

        # Add to conversation history
        self.messages.append({"role": "user", "content": context_message})

        # Build system prompt
        system = self._build_system_prompt(detected_tools)

        # Use non-streaming for tool calls, stream only final response
        return self._process_with_tools(system, stream)

    def _process_with_tools(self, system: str, stream: bool):
        """Process query, handling any tool calls."""
        while True:
            response = self.llm.chat(
                messages=self.messages,
                system=system,
                tools=TOOLS,
            )

            # If no tool calls, we're done
            if not response["tool_calls"]:
                if response["content"]:
                    self.messages.append({"role": "assistant", "content": response["content"]})
                if stream:
                    # Yield the content as a single chunk for consistency
                    yield response["content"]
                    return
                else:
                    return response["content"]

            # Handle tool calls
            tool_results = []
            assistant_content = []

            if response["content"]:
                assistant_content.append({"type": "text", "text": response["content"]})

            for tool_call in response["tool_calls"]:
                # Add tool use to assistant content
                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_call["id"],
                    "name": tool_call["name"],
                    "input": tool_call["input"],
                })

                # Execute the tool
                result = self._execute_tool(tool_call["name"], tool_call["input"])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call["id"],
                    "content": result,
                })

                # Yield tool execution info if streaming
                if stream:
                    yield f"[Tool: {tool_call['name']}] {result}\n"

            # Add assistant message with tool uses
            self.messages.append({"role": "assistant", "content": assistant_content})

            # Add tool results
            self.messages.append({"role": "user", "content": tool_results})

            # Continue loop to get final response after tool execution

    def reset(self):
        """Clear conversation history."""
        self.messages = []
        self.current_context = ""
