"""Abstract Search Provider interface."""
from abc import ABC, abstractmethod
from typing import List
from research_agent.schema import SearchResult


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    @abstractmethod
    async def search(self, query: str) -> List[SearchResult]:
        """
        Search for information on a given query.

        Args:
            query: Search query string

        Returns:
            List of SearchResult objects
        """
        pass
