"""
Command Router — parses intent and routes to the right handler.

Priority order (checked top → down):
  1. Greetings
  2. Time / Date
  3. Weather
  4. News
  5. Calendar (list + add)
  6. Notes (add / list / clear)
  7. Calculator
  8. Wikipedia
  9. Play song
  10. Open website (checks known list first)
  11. Open desktop app (fallback)
  12. PDF chat (if PDF is active)
  13. Exit
  → else: return None (LLM handles it)
"""
import datetime
import re
import webbrowser
from typing import Optional

from app.core.logger import get_logger
from app.core.i18n import lang_manager
from app.services.weather_service import weather_service
from app.services.news_service import news_service
from app.services.notes_service import notes_service
from app.services.calendar_service import calendar_service
from app.services.calendar_parser import parse_event
from app.services.pdf_service import pdf_service
from app.services.llm_service import llm_service
from app.services.jokes_service import jokes_service
from app.services.system_service import system_service
from app.services.image_service import image_service
from app.services.stats_service import stats_service
from app.services.image_gen_service import image_gen_service
from app.services.websearch_service import websearch_service
from app.services.messaging_service import messaging_service

log = get_logger(__name__)

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "stack overflow": "https://stackoverflow.com",
    "chatgpt": "https://chat.openai.com",
    "whatsapp": "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "linkedin": "https://www.linkedin.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "reddit": "https://www.reddit.com",
    "spotify": "https://open.spotify.com",
    "wikipedia": "https://www.wikipedia.org",
    "maps": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "translate": "https://translate.google.com",
    "google translate": "https://translate.google.com",
}


class CommandService:
    def handle(self, text: str) -> Optional[str]:
        if not text or not text.strip():
            return None
        raw = text.strip()
        t = raw.lower()

        try:
            result = self._route(raw, t)
            if result is not None:
                # Track first word as command type
                cmd_type = t.split()[0] if t.split() else "other"
                stats_service.track(cmd_type, is_llm=False)
            return result
        except Exception as e:
            log.exception("Command handler error: %s", e)
            return None  # fall through to LLM

    # ─────────────────────────────────────────────────────────
    def _route(self, raw: str, t: str) -> Optional[str]:
        # ── 1. GREETINGS ──
        greetings = ["hello", "hi ", "hey", "namaste", "नमस्ते", "नमस्कार",
                     "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "ਹੈਲੋ"]
        if len(raw) < 30 and (t in {"hi", "hello", "hey"} or
                               any(g in t for g in greetings)):
            return lang_manager.t("hello")

        # ── 2. CALCULATOR (must run BEFORE time-check, "times" contains "time") ──
        if re.search(r"\d", t) and any(w in t for w in [
            "calculate", "what is", "what's", "compute", "how much is",
            "+", "-", "*", "/", " times ", " plus ", " minus ",
            " divided ", " into ", " multiplied "
        ]):
            calc = self._try_calculate(t)
            if calc is not None:
                return lang_manager.t("answer_is", calc)

        # ── 3. TIME / DATE ──
        # Use \b for English (avoids "times"), plain substring for Devanagari/Gurmukhi
        has_english_time = bool(re.search(r"\b(time)\b", t))
        has_indic_time = any(k in t for k in ["समय", "टाइम", "ਸਮਾਂ", "ਟਾਈਮ"])
        if has_english_time or has_indic_time:
            return lang_manager.t("time_is", datetime.datetime.now().strftime("%I:%M %p"))

        has_english_date = bool(re.search(r"\b(date)\b", t))
        has_indic_date = any(k in t for k in ["तारीख", "ਤਾਰੀਖ"])
        if has_english_date or has_indic_date:
            return lang_manager.t("today_is", datetime.datetime.now().strftime("%A, %B %d, %Y"))

        if re.search(r"\b(what day|which day|day is it)\b", t) or \
           any(k in t for k in ["दिन", "ਦਿਨ"]):
            return lang_manager.t("day_is", datetime.datetime.now().strftime("%A"))

        # ── 3. WEATHER ──
        if "weather" in t or "temperature" in t or "मौसम" in t or "ਮੌਸਮ" in t:
            m = re.search(r"(?:weather|temperature|मौसम|ਮੌਸਮ)"
                          r"(?:\s+(?:in|at|for|is|of))?\s+([a-zA-Z\s]+?)"
                          r"(?:\s*[\?\.]|$)", t)
            location = m.group(1).strip() if m else ""
            return weather_service.get_weather(location)

        # ── 4. NEWS ──
        if "news" in t or "headlines" in t or "समाचार" in t or "ਖ਼ਬਰਾਂ" in t:
            m = re.search(r"news(?:\s+about|\s+on|\s+of)?\s+(.+?)(?:\s*[\?\.]|$)", t)
            topic = m.group(1).strip() if m else ""
            return news_service.get_headlines(topic=topic)

        # ── 5. CALENDAR ──
        cal_list_kws = ["my calendar", "my events", "upcoming events",
                        "what's on my calendar", "schedule today",
                        "what's my schedule", "any events"]
        if any(k in t for k in cal_list_kws):
            return calendar_service.list_events()

        cal_add_kws = ["schedule ", "add event", "book ", "create event",
                       "new event", "add to calendar"]
        if any(k in t for k in cal_add_kws):
            parsed = parse_event(t)
            if parsed:
                return calendar_service.add_event(parsed["title"], parsed["when"])
            return "Please say something like: 'schedule meeting tomorrow at 3pm'."

        # ── 6. NOTES ──
        if t.startswith(("add note", "new note", "remind me", "note:", "note that")):
            note = re.sub(
                r"^(add note|new note|remind me to|remind me|note that|note:)\s*",
                "", t
            ).strip()
            if note:
                return notes_service.add(note)
            return "Please tell me what note to add."

        if t in {"show notes", "list notes", "my notes", "read notes",
                 "what are my notes", "read my notes", "show my notes",
                 "list my notes", "display my notes", "display notes"}:
            return notes_service.list_spoken()

        if t in {"clear notes", "delete all notes", "remove all notes"}:
            return notes_service.clear()

        # ── 8. WIKIPEDIA ──
        if "wikipedia" in t or t.startswith(("who is ", "who was ",
                                              "tell me about ")):
            try:
                import wikipedia
                q = re.sub(r"^(wikipedia|who is|who was|tell me about)\s+", "", t).strip("?. ")
                if q:
                    return wikipedia.summary(q, sentences=2, auto_suggest=True, redirect=True)
            except Exception as e:
                log.warning("Wikipedia failed: %s", e)

        # ── 9. PLAY on YouTube ──
        if t.startswith("play ") and "youtube" not in t.split("play ")[1].split()[0:1]:
            song = t[5:].strip()
            if song:
                try:
                    import pywhatkit
                    pywhatkit.playonyt(song)
                    return lang_manager.t("playing_youtube", song)
                except Exception as e:
                    log.error("YouTube play failed: %s", e)
                    # Fallback: just open the search URL
                    webbrowser.open(
                        f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}"
                    )
                    return lang_manager.t("playing_youtube", song)

        # ── 10. OPEN WEBSITE ──
        open_kws = ["open ", "launch ", "go to ", "खोलो", "ਖੋਲ੍ਹੋ"]
        if any(k in t for k in open_kws):
            # Sort by length DESC so "google maps" wins over "google"
            for name in sorted(WEBSITES.keys(), key=len, reverse=True):
                if name in t:
                    log.info("Opening website: %s", WEBSITES[name])
                    webbrowser.open(WEBSITES[name])
                    return lang_manager.t("opening", name)

            # ── 11. Fallback: Open desktop app ──
            app_name = re.sub(r"^(open|launch|खोलो|ਖੋਲ੍ਹੋ)\s+", "", t).strip()
            if app_name:
                if self._try_open_app(app_name):
                    return lang_manager.t("opening", app_name)
                else:
                    return f"Sorry, I couldn't find an app called '{app_name}'."

        # ── IMAGE CHAT (if active image) ──
        if image_service.active:
            img_kws = ["the image", "the picture", "the photo", "in the image",
                       "in the picture", "what's in the image", "what do you see",
                       "describe the image", "describe the picture"]
            if any(k in t for k in img_kws):
                return image_service.ask(raw)

        # ── PDF CHAT (if active PDF and query looks like a PDF question) ──
        if pdf_service.active:
            pdf_kws = ["the pdf", "the document", "the file", "from the pdf",
                       "in the pdf", "in the document", "summarize", "summary",
                       "explain the document", "explain the pdf",
                       "what does the pdf say", "what does the document say"]
            if any(k in t for k in pdf_kws):
                context = pdf_service.get_context(t)
                if context:
                    return llm_service.chat_with_context(raw, context)

        # ── JOKES & QUOTES (offline, always works) ──
        if any(k in t for k in ["joke", "make me laugh", "मज़ाक", "ਮਜ਼ਾਕ"]):
            return jokes_service.joke(lang_manager.current)
        if any(k in t for k in ["quote", "motivate", "motivation",
                                 "inspire", "प्रेरणा", "ਪ੍ਰੇਰਨਾ"]):
            return jokes_service.quote(lang_manager.current)

        # ── IMAGE GENERATION ──
        img_gen_kws = ["draw ", "generate image", "generate a picture",
                       "create image", "create a picture", "paint ",
                       "imagine ", "make a picture of"]
        if any(k in t for k in img_gen_kws):
            prompt = re.sub(
                r"^(draw|generate image|generate a picture|create image|"
                r"create a picture|paint|imagine|make a picture of)\s+(a|an|the)?\s*",
                "", t
            ).strip()
            if prompt:
                try:
                    result = image_gen_service.generate(prompt)
                    return f"__IMAGE__:{result['url']}:{prompt}"
                except Exception as e:
                    return f"Sorry, image generation failed: {e}"

        # ── WEB SEARCH ──
        web_kws = ["search for", "search the web", "google ", "look up ",
                   "find information", "web search"]
        if any(k in t for k in web_kws):
            query = re.sub(
                r"^(search for|search the web for|search the web|"
                r"google|look up|find information about|web search)\s+",
                "", t
            ).strip("?.")
            if query:
                return websearch_service.search(query)

        # ── URL summarizer ──
        url_match = re.search(r"https?://\S+", raw)
        if url_match and any(k in t for k in ["summarize", "summary of", "what is"]):
            content = websearch_service.summarize_url(url_match.group(0))
            if content:
                return llm_service.chat_with_context(
                    "Summarize this article in 2-3 sentences.", content
                )
            return "Sorry, I couldn't fetch that URL."

        # ── EMAIL ──
        if any(k in t for k in ["send email", "email ", "compose email"]) and "@" in raw:
            parsed = messaging_service.parse_email_command(raw)
            return messaging_service.send_email(**parsed)

        # ── WHATSAPP ──
        if any(k in t for k in ["whatsapp", "send whatsapp", "wa message"]):
            parsed = messaging_service.parse_whatsapp_command(raw)
            return messaging_service.send_whatsapp(**parsed)

        # ── SYSTEM INFO ──
        if any(k in t for k in ["battery", "battery level", "battery status"]):
            return system_service.battery()
        if "cpu" in t and any(k in t for k in ["usage", "load", "status"]):
            return system_service.cpu()
        if any(k in t for k in ["memory usage", "ram usage", "memory status"]):
            return system_service.memory()
        if any(k in t for k in ["disk space", "disk usage", "storage"]):
            return system_service.disk()
        if any(k in t for k in ["screenshot", "screen shot", "capture screen"]):
            return system_service.screenshot()
        if any(k in t for k in ["system info", "os info", "which os", "operating system"]):
            return system_service.os_info()

        # ── 13. EXIT ──
        if t in {"exit", "quit", "stop", "bye", "goodbye",
                 "अलविदा", "ਅਲਵਿਦਾ"}:
            return lang_manager.t("goodbye")

        return None  # → LLM handles it

    # ─────────────────────────────────────────────────────────
    def _try_calculate(self, t: str) -> Optional[str]:
        """Safely evaluate a math expression from natural language."""
        expr = t
        # Word → symbol conversions
        replacements = [
            ("what is", ""), ("what's", ""), ("calculate", ""), ("compute", ""),
            ("plus", "+"), ("minus", "-"), ("times", "*"), (" x ", "*"),
            ("multiplied by", "*"), ("multiply", "*"),
            ("divided by", "/"), ("divide", "/"), ("into", "*"),
            ("?", ""),
        ]
        for old, new in replacements:
            expr = expr.replace(old, new)

        # Strip everything but digits, operators, parens, dot
        expr = re.sub(r"[^0-9+\-*/().\s]", "", expr).strip()
        if not expr or not re.match(r"^[\d+\-*/().\s]+$", expr):
            return None
        # Must have at least one digit and one operator to be a "calc"
        if not re.search(r"\d", expr) or not re.search(r"[+\-*/]", expr):
            return None

        try:
            result = eval(expr, {"__builtins__": {}}, {})
            if isinstance(result, float):
                # Prettify: 25.0 → "25", 3.14159 → "3.14"
                result = int(result) if result.is_integer() else round(result, 4)
            return str(result)
        except Exception:
            return None

    def _try_open_app(self, app_name: str) -> bool:
        """Try to open a Windows app; return True on success."""
        try:
            from AppOpener import open as app_open
            app_open(app_name, match_closest=True, throw_error=True)
            return True
        except Exception as e:
            log.warning("Could not open app '%s': %s", app_name, e)
            return False


command_service = CommandService()
