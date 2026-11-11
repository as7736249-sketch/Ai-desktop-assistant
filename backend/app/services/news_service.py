"""News Service — uses Google News RSS (free, no API key)."""
import re
import requests
from xml.etree import ElementTree as ET

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)


class NewsService:
    BASE = "https://news.google.com/rss"
    TIMEOUT = 10

    def get_headlines(self, topic: str = "", count: int = 5) -> str:
        country = settings.NEWS_COUNTRY
        try:
            if topic.strip():
                q = topic.strip().replace(" ", "+")
                url = f"{self.BASE}/search?q={q}&hl=en-IN&gl={country}&ceid={country}:en"
            else:
                url = f"{self.BASE}?hl=en-IN&gl={country}&ceid={country}:en"

            r = requests.get(url, timeout=self.TIMEOUT,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()

            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:count]
            if not items:
                return "No news headlines found."

            headlines = []
            for i, item in enumerate(items, 1):
                title_el = item.find("title")
                title = title_el.text if title_el is not None and title_el.text else ""
                # Strip publisher suffix e.g., " - The Times of India"
                title = re.sub(r"\s*-\s*[^-]+$", "", title).strip()
                if title:
                    headlines.append(f"{i}. {title}")

            if not headlines:
                return "No news headlines found."

            prefix = f"Top news{' about ' + topic if topic else ''}: "
            return prefix + " ... ".join(headlines)
        except requests.Timeout:
            log.error("News timeout")
            return "News service timed out."
        except Exception as e:
            log.error("News lookup failed: %s", e)
            return "Sorry, I couldn't fetch the news right now."


news_service = NewsService()
