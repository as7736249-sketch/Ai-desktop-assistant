"""
Messaging Service — opens Gmail Compose / WhatsApp Web with pre-filled content.

Uses browser URL scheme (no OAuth needed).
"""
import re
import webbrowser
from urllib.parse import quote

from app.core.logger import get_logger

log = get_logger(__name__)


class MessagingService:

    def send_email(self, to: str = "", subject: str = "", body: str = "") -> str:
        """Open Gmail compose with pre-filled fields."""
        params = []
        if to:      params.append(f"to={quote(to)}")
        if subject: params.append(f"su={quote(subject)}")
        if body:    params.append(f"body={quote(body)}")
        url = "https://mail.google.com/mail/?view=cm&fs=1&" + "&".join(params) if params \
              else "https://mail.google.com/mail/?view=cm&fs=1"
        log.info("Opening Gmail compose: to=%s subject=%s", to[:30], subject[:30])
        webbrowser.open(url)
        who = f" to {to}" if to else ""
        return f"Opened Gmail compose{who}. Review and hit Send in your browser."

    def send_whatsapp(self, phone: str = "", message: str = "") -> str:
        """Open WhatsApp Web with message."""
        phone_clean = re.sub(r"\D", "", phone)
        url = f"https://web.whatsapp.com/send?text={quote(message)}"
        if phone_clean:
            url = f"https://web.whatsapp.com/send?phone={phone_clean}&text={quote(message)}"
        log.info("Opening WhatsApp: phone=%s", phone_clean[:8])
        webbrowser.open(url)
        return f"Opened WhatsApp Web. Review and hit Send."

    @staticmethod
    def parse_email_command(text: str) -> dict:
        """
        Parse: "email john@example.com about meeting: let's meet at 3pm"
        Or:    "send email to alice subject: hello body: how are you"
        """
        t = text.lower()
        # Extract email address
        email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
        to = email_match.group(0) if email_match else ""

        # Subject
        sub_match = re.search(r"(?:about|subject:?|regarding)\s+(.+?)(?:\s+body:?|\s+message:?|\s*[:.]|$)", t)
        subject = sub_match.group(1).strip() if sub_match else ""

        # Body (everything after ": " or "saying")
        body_match = re.search(r"(?:saying|body:?|message:?|:\s+)(.+)$", text, re.IGNORECASE)
        body = body_match.group(1).strip() if body_match else ""

        return {"to": to, "subject": subject.title(), "body": body}

    @staticmethod
    def parse_whatsapp_command(text: str) -> dict:
        """
        Parse: "whatsapp 9876543210: hey what's up"
        Or:    "send whatsapp to +91 98765 43210 saying hello"
        """
        phone_match = re.search(r"[\+\d\s\-]{7,}", text)
        phone = phone_match.group(0) if phone_match else ""

        msg_match = re.search(r"(?:saying|message:?|:\s+)(.+)$", text, re.IGNORECASE)
        message = msg_match.group(1).strip() if msg_match else ""

        return {"phone": phone, "message": message}


messaging_service = MessagingService()
