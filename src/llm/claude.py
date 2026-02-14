import os
import time
from typing import Generator, Optional

from anthropic import Anthropic, RateLimitError

from .base import BaseLLM


class ClaudeLLM(BaseLLM):
    """Claude API implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.model = model
        self.client = Anthropic(api_key=self.api_key)

    def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        max_retries: int = 3,
    ) -> dict:
        """Send a chat request to Claude with retry on rate limit."""
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        # Retry with exponential backoff on rate limit
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(**kwargs)
                break
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt * 10  # 10s, 20s, 40s
                print(f"\n[Rate limit hit, waiting {wait_time}s...]", flush=True)
                time.sleep(wait_time)

        # Parse response into standard format
        result = {
            "content": "",
            "tool_calls": [],
            "stop_reason": response.stop_reason,
        }

        for block in response.content:
            if block.type == "text":
                result["content"] += block.text
            elif block.type == "tool_use":
                result["tool_calls"].append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

        return result

    def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> Generator[str, None, None]:
        """Stream a chat response from Claude."""
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }

        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
