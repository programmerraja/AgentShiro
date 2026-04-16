"""HTTP fetch provider for fetching and parsing URLs."""
import re
import aiohttp
from research_agent.providers.fetch_provider import FetchProvider


class HTTPFetch(FetchProvider):
    """Fetch provider using HTTP with HTML stripping."""

    async def fetch(self, url: str) -> str:
        """
        Fetch URL and return cleaned text content.

        Args:
            url: URL to fetch

        Returns:
            Cleaned text content
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status != 200:
                        return ""

                    html = await response.text()

                    # Remove script tags
                    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)

                    # Remove style tags
                    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

                    # Remove HTML tags
                    html = re.sub(r"<[^>]+>", " ", html)

                    # Normalize whitespace
                    html = re.sub(r"\s+", " ", html)

                    return html.strip()

        except Exception as e:
            print(f"HTTP fetch error: {e}")
            return ""
