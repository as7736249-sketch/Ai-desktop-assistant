"""Notes / To-do Service — atomic JSON storage."""
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import List, Dict

from app.core.config import DATA_DIR
from app.core.logger import get_logger
from app.core.i18n import lang_manager

log = get_logger(__name__)
STORE = DATA_DIR / "notes.json"


class NotesService:
    def __init__(self):
        self._lock = Lock()
        if not STORE.exists():
            self._save([])

    def _load(self) -> List[Dict]:
        try:
            with self._lock:
                return json.loads(STORE.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning("Failed to load notes.json (resetting): %s", e)
            return []

    def _save(self, data: List[Dict]) -> None:
        """Atomic write: write to tmp file then rename."""
        with self._lock:
            fd, tmp = tempfile.mkstemp(dir=str(STORE.parent), suffix=".json.tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp, STORE)
            except Exception:
                if os.path.exists(tmp):
                    os.unlink(tmp)
                raise

    def add(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "Please provide the note text."
        data = self._load()
        note = {
            "id": int(datetime.now().timestamp() * 1000),
            "text": text,
            "done": False,
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        data.append(note)
        self._save(data)
        return lang_manager.t("note_added", text)

    def list_all(self):
        return self._load()

    def list_spoken(self) -> str:
        data = self._load()
        pending = [n for n in data if not n.get("done")]
        if not pending:
            return lang_manager.t("no_notes")
        items = [f"{i+1}. {n['text']}" for i, n in enumerate(pending[:10])]
        prefix = "Your notes: " if lang_manager.current == "en" else ""
        return prefix + " ... ".join(items)

    def toggle(self, note_id: int) -> bool:
        data = self._load()
        for n in data:
            if n["id"] == note_id:
                n["done"] = not n.get("done", False)
                self._save(data)
                return True
        return False

    def delete(self, note_id: int) -> bool:
        data = self._load()
        new = [n for n in data if n["id"] != note_id]
        if len(new) == len(data):
            return False
        self._save(new)
        return True

    def clear(self) -> str:
        self._save([])
        return lang_manager.t("notes_cleared")


notes_service = NotesService()
