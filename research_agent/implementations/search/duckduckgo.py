"""DuckDuckGo search provider using HTML lite interface (free, no API key required)."""
from typing import List
import aiohttp
import re
import asyncio
import time
from research_agent.providers.search_provider import SearchProvider
from research_agent.schema import SearchResult


class DuckDuckGoSearch(SearchProvider):
    """DuckDuckGo search using regular HTML interface."""

    # Global rate limiter: 2 second delay between requests
    _last_request_time = 0
    _rate_limit_lock = asyncio.Lock()

    async def search(self, query: str) -> List[SearchResult]:
        """
        Search using DuckDuckGo HTML interface.

        Args:
            query: Search query

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            return []

        try:
            # Enforce rate limit (2 seconds between requests to avoid blocks)
            async with self._rate_limit_lock:
                elapsed = time.time() - DuckDuckGoSearch._last_request_time
                if elapsed < 2.0:
                    await asyncio.sleep(2.0 - elapsed)
                DuckDuckGoSearch._last_request_time = time.time()

            # Use regular DuckDuckGo with HTML parameters
            endpoint = "https://duckduckgo.com/html"

            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://duckduckgo.com/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            params = {"q": query}

            delay = 1
            max_retries = 3
            retries = 0

            async with aiohttp.ClientSession() as session:
                while retries < max_retries:
                    try:
                        async with session.get(
                            endpoint,
                            params=params,
                            headers=headers,
                            timeout=aiohttp.ClientTimeout(total=15),
                            ssl=False
                        ) as response:
                            if response.status == 200:
                                html = await response.text()
                                results = self._parse_html_results(html)
                                return results
                            elif response.status in (429, 202):  # Rate limited or challenge
                                await asyncio.sleep(delay)
                                if delay < 10:
                                    delay *= 2
                                retries += 1
                                continue
                            else:
                                return []
                    except asyncio.TimeoutError:
                        return []

            return []

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    def _parse_html_results(self, html: str) -> List[SearchResult]:
        """Extract search results from DuckDuckGo HTML."""
        results = []
        seen_urls = set()

        # Pattern for DuckDuckGo's HTML format with uddg parameter
        # Matches: <a ... href="//duckduckgo.com/l/?uddg=...">TITLE</a>
        result_pattern = re.compile(
            r'<a[^>]*href=["\']([^"\']*uddg[^"\']*)["\'][^>]*>([^<]+)</a>',
            re.IGNORECASE
        )

        # Pattern to extract actual URL from uddg parameter
        uddg_pattern = re.compile(r'uddg=([^&]+)')

        matches = result_pattern.findall(html)

        for redirect_url, title in matches:
            title = self._clean_html(title.strip())

            # Skip empty titles or domain breadcrumbs
            if not title or len(title) < 3:
                continue

            # Skip if title looks like a domain/breadcrumb (all lowercase, contains domain-like pattern)
            if title.startswith("www.") or (title.count("/") > 0 and len(title) < 50):
                continue

            # Extract actual URL from uddg parameter
            url_str = redirect_url
            uddg_match = uddg_pattern.search(redirect_url)
            if uddg_match:
                try:
                    from urllib.parse import unquote
                    encoded_url = uddg_match.group(1)
                    url_str = unquote(encoded_url)
                except (ValueError, AttributeError):
                    url_str = redirect_url

            # Skip DuckDuckGo internal links
            if "duckduckgo.com" in url_str and "uddg" in url_str:
                continue

            # Deduplicate by URL
            if url_str in seen_urls:
                continue
            seen_urls.add(url_str)

            results.append(SearchResult(
                title=title,
                url=url_str,
                snippet=""
            ))

            if len(results) >= 5:
                break

        # Fallback if no results found
        if not results:
            results = self._fallback_parse(html)

        return results

    def _fallback_parse(self, html: str) -> List[SearchResult]:
        """Fallback parsing with simpler approach."""
        results = []

        # Look for DuckDuckGo's uddg redirect links
        uddg_pattern = re.compile(r'//duckduckgo\.com/l/\?uddg=([^"\'&]+)')
        matches = uddg_pattern.findall(html)

        seen_urls = set()
        for encoded_url in matches:
            try:
                from urllib.parse import unquote
                url_str = unquote(encoded_url)
            except (ValueError, AttributeError):
                url_str = encoded_url

            # Skip if we've seen this URL
            if url_str in seen_urls:
                continue
            seen_urls.add(url_str)

            # Find corresponding title - look backwards for the most recent link text
            # This is a simplified approach - in real parsing we'd match pairs better
            title_pattern = re.compile(rf'>([^<]+)<a[^>]*href=["\'][^"\']*{re.escape(encoded_url)}')
            title_match = title_pattern.search(html)

            if title_match:
                title = self._clean_html(title_match.group(1))
            else:
                # Extract title from URL domain
                title = url_str.split('/')[2] if '/' in url_str else url_str

            if not title or len(title) < 3:
                continue

            results.append(SearchResult(
                title=title,
                url=url_str,
                snippet=""
            ))

            if len(results) >= 5:
                break

        return results

    def _clean_html(self, text: str) -> str:
        """Remove HTML entities and tags."""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode common entities
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")
        text = text.replace("&nbsp;", " ")

        return text.strip()
