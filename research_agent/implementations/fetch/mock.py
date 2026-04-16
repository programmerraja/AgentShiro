"""Mock fetch provider for testing."""
from research_agent.providers.fetch_provider import FetchProvider


class MockFetch(FetchProvider):
    """Mock fetch provider for testing without actual HTTP calls."""

    def __init__(self, mock_content: str = ""):
        """Initialize with optional mock content."""
        self.mock_content = mock_content

    async def fetch(self, url: str) -> str:
        """Return predefined mock content."""
        return self.mock_content
