"""Mock LLM provider for testing."""
from research_agent.providers.llm_provider import LLMProvider
from research_agent.schema import LLMResponse


class MockLLM(LLMProvider):
    """Mock LLM provider for testing without API calls."""

    def __init__(self, responses: dict = None):
        """
        Initialize mock LLM with optional predefined responses.

        Args:
            responses: Dict mapping system prompts to responses
        """
        self.responses = responses or {}
        self.call_count = 0

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return mock response based on system prompt."""
        self.call_count += 1

        # Return different responses based on prompt content
        if "planner" in system_prompt.lower():
            return LLMResponse(
                text="Action: Search\nQuery: test query",
                cost=0.001
            )
        elif "synthesizer" in system_prompt.lower():
            return LLMResponse(
                text="Synthesized knowledge from search results.",
                cost=0.001
            )
        elif "extractor" in system_prompt.lower():
            return LLMResponse(
                text="- Fact 1 extracted\n- Fact 2 extracted\n- Fact 3 extracted",
                cost=0.001
            )
        elif "neighbor" in system_prompt.lower():
            return LLMResponse(
                text="1. Follow-up query 1\n2. Follow-up query 2",
                cost=0.001
            )
        else:  # finalizer or default
            return LLMResponse(
                text="This is the final answer based on research.",
                cost=0.002
            )
