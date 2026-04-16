"""Main ResearchAgent class."""

from typing import List, Optional
from research_agent.providers.llm_provider import LLMProvider
from research_agent.providers.search_provider import SearchProvider
from research_agent.providers.fetch_provider import FetchProvider
from research_agent.schema import Result
from research_agent.strategies import ScratchpadStrategy, GraphReaderStrategy, Strategy
from research_agent.implementations.llm import LiteLLMProvider
from research_agent.implementations.search import DuckDuckGoSearch
from research_agent.implementations.fetch import HTTPFetch


class ResearchAgent:
    """
    Research Agent that answers questions through iterative search and synthesis.

    Extends the base AgentShiro.Agent concept with research-specific functionality.
    Uses pluggable providers (LLM, Search, Fetch) and interchangeable strategies.
    """

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        strategy: str = "scratchpad",
        llm_provider: Optional[LLMProvider] = None,
        search_provider: Optional[SearchProvider] = None,
        fetch_provider: Optional[FetchProvider] = None,
        max_iterations: int = 5,
    ):
        """
        Initialize ResearchAgent.

        Args:
            model_name: LLM model to use (passed to LiteLLMProvider if no provider given)
            strategy: "scratchpad" or "graph-reader"
            llm_provider: Custom LLMProvider (uses LiteLLMProvider by default)
            search_provider: Custom SearchProvider (uses DuckDuckGoSearch by default)
            fetch_provider: Custom FetchProvider (uses HTTPFetch by default)
            max_iterations: Max iterations for strategies
        """
        self.model_name = model_name
        self.strategy_name = strategy
        self.max_iterations = max_iterations

        # Initialize providers with defaults
        self.llm_provider = llm_provider or LiteLLMProvider(model_name=model_name)
        self.search_provider = search_provider or DuckDuckGoSearch()
        self.fetch_provider = fetch_provider or HTTPFetch()

    async def answer(self, question: str, knowledge: str = "") -> Result:
        """
        Answer a research question using the configured strategy.

        Args:
            question: The research question
            knowledge: Optional prior knowledge to reuse

        Returns:
            Result object with answer, cost, and collected knowledge
        """
        strategy = self._resolve_strategy()
        print(f"\n🚀 Using strategy: {strategy.name()}")

        return await strategy.answer(question)

    def _resolve_strategy(self) -> Strategy:
        """Resolve strategy instance based on strategy_name."""
        if self.strategy_name == "scratchpad":
            return ScratchpadStrategy(self)
        elif self.strategy_name == "graph-reader":
            return GraphReaderStrategy(self)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy_name}")

    def set_llm_provider(self, provider: LLMProvider):
        """Set a custom LLM provider."""
        self.llm_provider = provider

    def set_search_provider(self, provider: SearchProvider):
        """Set a custom search provider."""
        self.search_provider = provider

    def set_fetch_provider(self, provider: FetchProvider):
        """Set a custom fetch provider."""
        self.fetch_provider = provider
