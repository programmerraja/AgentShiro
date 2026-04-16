"""Abstract Fetch Provider interface."""
from abc import ABC, abstractmethod


class FetchProvider(ABC):
    """Abstract base class for fetch providers."""

    @abstractmethod
    async def fetch(self, url: str) -> str:
        """
        Fetch and parse content from a URL.

        Args:
            url: URL to fetch

        Returns:
            Cleaned text content from the URL
        """
        pass
