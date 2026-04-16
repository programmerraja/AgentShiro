"""Search provider implementations."""

from .duckduckgo import DuckDuckGoSearch
from .mock import MockSearch

__all__ = ["DuckDuckGoSearch", "MockSearch"]
