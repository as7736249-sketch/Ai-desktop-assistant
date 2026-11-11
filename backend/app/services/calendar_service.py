"""
Google Calendar Service.

SETUP (one-time, optional):
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable "Google Calendar API"
  3. Create OAuth 2.0 credentials (type: Desktop app)
  4. Download credentials.json → put in backend/ folder
  5. First run opens a browser to authorize.

If credentials.json is missing, this service returns friendly errors.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings, BACKEND_DIR
from app.core.logger import get_logger

log = get_logger(__name__)

CRED_FILE = BACKEND_DIR / "credentials.json"
TOKEN_FILE = BACKEND_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarService:
    def __init__(self):
        self.service = None
        self.enabled = False
        self.setup_message: str = ""
        if settings.ENABLE_CALENDAR:
            self._try_connect()
        else:
            self.setup_message = "Calendar feature is disabled in settings."

    def _try_connect(self):
        if not CRED_FILE.exists():
            self.setup_message = (
                "Google Calendar is not set up. To enable it, place "
                "credentials.json in the backend folder. See README for steps."
            )
            log.info("Calendar: credentials.json not found (feature disabled)")
            return
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None
            if TOKEN_FILE.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                except Exception as e:
                    log.warning("token.json invalid, will re-auth: %s", e)
                    creds = None

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception:
                        creds = None
                if not creds:
                    flow = InstalledAppFlow.from_client_secrets_file(str(CRED_FILE), SCOPES)
                    creds = flow.run_local_server(port=0)
                TOKEN_FILE.write_text(creds.to_json())

            self.service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            self.enabled = True
            log.info("✅ Google Calendar connected")
        except ImportError as e:
            self.setup_message = "Google Calendar libraries not installed."
            log.warning("Calendar libs missing: %s", e)
        except Exception as e:
            self.setup_message = f"Calendar setup failed: {e}"
            log.error("Calendar init failed: %s", e)

    def _check(self) -> Optional[str]:
        if not self.enabled:
            return self.setup_message or "Google Calendar is not available."
        return None

    def list_events(self, max_results: int = 5) -> str:
        err = self._check()
        if err:
            return err
        try:
            now = datetime.now(timezone.utc).isoformat()
            events_result = self.service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            events = events_result.get("items", [])
            if not events:
                return "You have no upcoming events."

            lines = []
            for ev in events:
                start = ev["start"].get("dateTime", ev["start"].get("date"))
                summary = ev.get("summary", "(no title)")
                try:
                    dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                    when = dt.strftime("%b %d, %I:%M %p")
                except Exception:
                    when = start
                lines.append(f"{summary} on {when}")
            return "Your upcoming events: " + ". ".join(lines)
        except Exception as e:
            log.error("List events failed: %s", e)
            return "Sorry, I couldn't fetch your calendar."

    def add_event(self, title: str, when: datetime, duration_min: int = 60) -> str:
        err = self._check()
        if err:
            return err
        try:
            event = {
                "summary": title,
                "start": {"dateTime": when.isoformat(), "timeZone": settings.TIMEZONE},
                "end": {
                    "dateTime": (when + timedelta(minutes=duration_min)).isoformat(),
                    "timeZone": settings.TIMEZONE,
                },
            }
            self.service.events().insert(calendarId="primary", body=event).execute()
            return f"Added '{title}' to your calendar on {when.strftime('%b %d at %I:%M %p')}."
        except Exception as e:
            log.error("Add event failed: %s", e)
            return "Sorry, I couldn't add that event."


calendar_service = CalendarService()
