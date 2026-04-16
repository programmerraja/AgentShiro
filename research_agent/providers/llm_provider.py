"""Abstract LLM Provider interface."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from research_agent.schema import LLMResponse


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Generate a response using the LLM.

        Args:
            system_prompt: System context for the LLM
            user_prompt: User's input/question

        Returns:
            LLMResponse with generated text and cost tracking
        """
        pass
