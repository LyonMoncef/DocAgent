from abc import ABC, abstractmethod
from typing import Generator, Optional


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> dict:
        """
        Send a chat request and return the response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: Optional system prompt
            tools: Optional list of tool definitions

        Returns:
            Response dict with 'content', 'tool_calls', 'stop_reason'
        """
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[dict],
        system: Optional[str] = None,
        tools: Optional[list[dict]] = None,
    ) -> Generator[str, None, None]:
        """
        Stream a chat response.

        Yields:
            Text chunks as they arrive
        """
        pass
