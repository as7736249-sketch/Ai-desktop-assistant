"""
Weather Service — uses wttr.in (free, no API key).
"""
import requests

from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)


class WeatherService:
    BASE = "https://wttr.in"
    TIMEOUT = 12

    def get_weather(self, location: str = "") -> str:
        location = (location or "").strip() or settings.DEFAULT_LOCATION
        loc = location.replace(" ", "+")
        url = f"{self.BASE}/{loc}?format=j1"
        try:
            r = requests.get(url, timeout=self.TIMEOUT,
                             headers={"User-Agent": "curl/8.0"})
            r.raise_for_status()
            data = r.json()

            current = data["current_condition"][0]
            area_info = data["nearest_area"][0]
            area = area_info["areaName"][0]["value"]
            country = area_info["country"][0]["value"]

            temp_c = current["temp_C"]
            feels = current["FeelsLikeC"]
            desc = current["weatherDesc"][0]["value"]
            humidity = current["humidity"]
            wind = current["windspeedKmph"]

            return (
                f"Weather in {area}, {country}: {desc}. "
                f"Temperature {temp_c} degrees Celsius, feels like {feels}. "
                f"Humidity {humidity} percent, wind {wind} kilometers per hour."
            )
        except requests.Timeout:
            log.error("Weather timeout for '%s'", location)
            return "Weather service timed out. Please try again."
        except requests.HTTPError as e:
            log.error("Weather HTTP error: %s", e)
            return f"Could not find weather for '{location}'."
        except Exception as e:
            log.error("Weather lookup failed: %s", e)
            return "Sorry, I couldn't fetch the weather right now."


weather_service = WeatherService()
