"""Export chat history as Markdown."""
from datetime import datetime
from typing import List, Dict

from app.core.config import settings


class ExportService:
    def to_markdown(self, messages: List[Dict[str, str]]) -> str:
        lines = [
            f"# {settings.APP_NAME} Chat Export",
            f"_Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
            f"_Total messages: {len(messages)}_",
            "",
            "---",
            "",
        ]
        for m in messages:
            who = m.get("who", "assistant")
            text = m.get("text", "")
            prefix = "🙂 **You**" if who == "user" else "🤖 **Jarvis**"
            lines.append(f"### {prefix}")
            lines.append("")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)


export_service = ExportService()
