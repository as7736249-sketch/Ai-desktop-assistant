"""
Web Search Service — uses DuckDuckGo Instant Answers + HTML search.
No API key needed!
"""
import re
from typing import List
from urllib.parse import quote

import requests

from app.core.logger import get_logger

log = get_logger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Jarvis/5.0)"}


class WebSearchService:
    TIMEOUT = 10

    def search(self, query: str, max_results: int = 5) -> str:
        """Return a human-readable summary of top web results."""
        query = (query or "").strip()
        if not query:
            return "Please provide a search query."

        # 1. Try DuckDuckGo Instant Answer API (great for facts)
        instant = self._instant_answer(query)
        if instant:
            return instant

        # 2. Fallback: scrape the HTML results page
        results = self._html_search(query, max_results)
        if not results:
            return f"No results found for '{query}'."

        lines = [f"Top results for '{query}':"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']} — {r['snippet']}")
        return " ... ".join(lines)

    def _instant_answer(self, query: str) -> str:
        try:
            url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
            r = requests.get(url, headers=HEADERS, timeout=self.TIMEOUT)
            r.raise_for_status()
            data = r.json()
            if data.get("AbstractText"):
                return data["AbstractText"]
            if data.get("Answer"):
                return str(data["Answer"])
            if data.get("Definition"):
                return data["Definition"]
        except Exception as e:
            log.debug("Instant answer failed: %s", e)
        return ""

    def _html_search(self, query: str, max_results: int) -> List[dict]:
        """Fallback: scrape DDG HTML results."""
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            r = requests.post(url, headers=HEADERS, timeout=self.TIMEOUT,
                              data={"q": query})
            r.raise_for_status()
            html = r.text

            # Simple regex — good enough for DDG's structure
            pattern = r'<a[^>]*class="result__a"[^>]*>([^<]+)</a>.*?<a[^>]*class="result__snippet"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, html, re.DOTALL)[:max_results]
            return [
                {"title": self._clean(t), "snippet": self._clean(s)}
                for t, s in matches
            ]
        except Exception as e:
            log.warning("HTML search failed: %s", e)
            return []

    def _clean(self, s: str) -> str:
        s = re.sub(r"<[^>]+>", "", s)  # strip tags
        s = re.sub(r"\s+", " ", s).strip()
        return s[:200]

    def summarize_url(self, url: str) -> str:
        """Fetch a URL and return its text content (for LLM summarization)."""
        try:
            r = requests.get(url, headers=HEADERS, timeout=self.TIMEOUT)
            r.raise_for_status()
            html = r.text
            # Remove scripts, styles, HTML tags
            html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
            html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.I)
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:6000]  # first 6000 chars is plenty for LLM
        except Exception as e:
            log.error("URL fetch failed: %s", e)
            return ""


websearch_service = WebSearchService()
