"""
Natural-language parser for calendar commands.
Handles:
  - "schedule meeting tomorrow at 3pm"
  - "add event lunch today at 1pm"
  - "book dentist next monday at 10am"
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple

DAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def parse_time_str(s: str) -> Optional[Tuple[int, int]]:
    """Parse '3pm', '3:30pm', '15:00' → (hour, minute)."""
    s = s.strip().lower().replace(" ", "")
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", s)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = m.group(3)
    if ampm == "pm" and hour < 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return (hour, minute)
    return None


def parse_date(text: str) -> datetime:
    """Return a datetime whose date component is what the user meant."""
    now = datetime.now()
    text = text.lower()

    if "day after tomorrow" in text:
        return now + timedelta(days=2)
    if "tomorrow" in text:
        return now + timedelta(days=1)
    if "today" in text or "tonight" in text:
        return now

    for name, idx in DAYS.items():
        if name in text:
            diff = (idx - now.weekday()) % 7
            if diff == 0:  # same day of week → next week
                diff = 7
            return now + timedelta(days=diff)
    return now  # default: today


def parse_event(text: str) -> Optional[dict]:
    """
    Parse "schedule|add|book|create <title> [today|tomorrow|monday...] at <time>".
    Returns {"title": str, "when": datetime} or None if unparseable.
    """
    t = text.lower().strip()

    # Time (required)
    time_match = re.search(r"at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", t)
    if not time_match:
        return None
    parsed_time = parse_time_str(time_match.group(1))
    if not parsed_time:
        return None
    hour, minute = parsed_time

    # Date
    when = parse_date(t)
    when = when.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If time already passed today, push to tomorrow
    if when < datetime.now() and "tomorrow" not in t and "next" not in t:
        # Only push if it's for "today" implicitly
        no_date = not any(
            w in t for w in ["tomorrow", "monday", "tuesday", "wednesday",
                             "thursday", "friday", "saturday", "sunday", "next"]
        )
        if no_date:
            when = when + timedelta(days=1)

    # Extract title
    title_match = re.search(
        r"(?:schedule|add event|add|book|create event|create|new event|calendar)\s+(.+?)\s+(?:at\s+\d|today|tomorrow|tonight|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next)",
        t,
    )
    title = (title_match.group(1).strip() if title_match else "Untitled event")
    title = re.sub(r"^(a|an|the)\s+", "", title).strip() or "Event"
    title = title.title()

    return {"title": title, "when": when}
