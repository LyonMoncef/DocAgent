import os
from glob import glob
from pathlib import Path
from typing import Optional

import yaml


class ConfigLoader:
    def __init__(self, tools_yaml_path: str = "config/tools.yaml"):
        self.tools_yaml_path = tools_yaml_path
        self.tools = self._load_tools_config()

    def _load_tools_config(self) -> dict:
        with open(self.tools_yaml_path, "r") as f:
            data = yaml.safe_load(f)
        return data.get("tools", {})

    def _expand_path(self, path: str) -> list[str]:
        """Expand ~ and resolve glob patterns, return list of actual file paths."""
        expanded = os.path.expanduser(path)
        if "*" in expanded:
            return glob(expanded, recursive=True)
        elif os.path.exists(expanded):
            return [expanded]
        return []

    def list_tools(self) -> list[str]:
        """Return list of available tool names."""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> Optional[dict]:
        """Get tool metadata (name, description, paths)."""
        return self.tools.get(tool_name)

    def get_tool_files(self, tool_name: str) -> dict[str, str]:
        """
        Load all config files for a tool.
        Returns dict of {filepath: content}
        """
        tool = self.tools.get(tool_name)
        if not tool:
            return {}

        files = {}
        for path_pattern in tool.get("paths", []):
            for filepath in self._expand_path(path_pattern):
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, "r") as f:
                            files[filepath] = f.read()
                    except Exception as e:
                        files[filepath] = f"[Error reading file: {e}]"
        return files

    def find_tool_by_keyword(self, keyword: str) -> Optional[str]:
        """
        Find a tool by keyword/alias.
        e.g., 'vim', 'neovim', 'nvim' all match 'nvim'
        """
        keyword = keyword.lower()

        # Direct match
        if keyword in self.tools:
            return keyword

        # Check name and description
        for tool_key, tool_data in self.tools.items():
            name = tool_data.get("name", "").lower()
            desc = tool_data.get("description", "").lower()
            if keyword in name or keyword in desc or keyword in tool_key:
                return tool_key

        # Common aliases
        aliases = {
            "vim": "nvim",
            "neovim": "nvim",
            "shell": "zsh",
            "terminal": "tmux",
        }
        return aliases.get(keyword)

    def build_context(self, tool_names: list[str]) -> str:
        """
        Build a formatted context string for the given tools.
        Used to inject into LLM prompt.
        """
        context_parts = []

        for tool_name in tool_names:
            tool_info = self.get_tool_info(tool_name)
            if not tool_info:
                continue

            files = self.get_tool_files(tool_name)
            if not files:
                continue

            context_parts.append(f"# {tool_info.get('name', tool_name)} Configuration")
            context_parts.append(f"_{tool_info.get('description', '')}_\n")

            for filepath, content in files.items():
                # Shorten path for display
                short_path = filepath.replace(os.path.expanduser("~"), "~")
                context_parts.append(f"## {short_path}")
                context_parts.append(f"```\n{content}\n```\n")

        return "\n".join(context_parts)
