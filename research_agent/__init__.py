"""Research Agent - AI-powered research automation."""

from research_agent.agent import ResearchAgent
from research_agent.schema import (
    SearchResult,
    LLMResponse,
    Result,
    Scratchpad,
    AtomicFact,
    Notebook
)
from research_agent.providers import (
    LLMProvider,
    SearchProvider,
    FetchProvider
)
from research_agent.implementations.llm import LiteLLMProvider, MockLLM
from research_agent.implementations.search import DuckDuckGoSearch, MockSearch
from research_agent.implementations.fetch import HTTPFetch, MockFetch
from research_agent.strategies import (
    Strategy,
    ScratchpadStrategy,
    GraphReaderStrategy
)

__all__ = [
    "ResearchAgent",
    "SearchResult",
    "LLMResponse",
    "Result",
    "Scratchpad",
    "AtomicFact",
    "Notebook",
    "LLMProvider",
    "SearchProvider",
    "FetchProvider",
    "LiteLLMProvider",
    "MockLLM",
    "DuckDuckGoSearch",
    "MockSearch",
    "HTTPFetch",
    "MockFetch",
    "Strategy",
    "ScratchpadStrategy",
    "GraphReaderStrategy"
]
