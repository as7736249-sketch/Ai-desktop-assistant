"""
Usage statistics service — tracks commands, sessions, most-used features.
Persists to a JSON file. Read-heavy, write cheap.
"""
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, date
from threading import Lock

from app.core.config import DATA_DIR
from app.core.logger import get_logger

log = get_logger(__name__)
STATS_FILE = DATA_DIR / "stats.json"


class StatsService:
    def __init__(self):
        self._lock = Lock()
        if not STATS_FILE.exists():
            self._save({
                "total_commands": 0,
                "total_llm_calls": 0,
                "commands": {},      # command_type → count
                "daily": {},         # YYYY-MM-DD → count
                "first_use": datetime.now().isoformat(timespec="seconds"),
                "last_use": datetime.now().isoformat(timespec="seconds"),
            })

    def _load(self):
        try:
            with self._lock:
                return json.loads(STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"total_commands": 0, "commands": {}, "daily": {}}

    def _save(self, data):
        with self._lock:
            fd, tmp = tempfile.mkstemp(dir=str(STATS_FILE.parent), suffix=".json.tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp, STATS_FILE)
            except Exception:
                if os.path.exists(tmp):
                    os.unlink(tmp)

    def track(self, command_type: str, is_llm: bool = False):
        try:
            data = self._load()
            data["total_commands"] = data.get("total_commands", 0) + 1
            if is_llm:
                data["total_llm_calls"] = data.get("total_llm_calls", 0) + 1
            data.setdefault("commands", {})
            data["commands"][command_type] = data["commands"].get(command_type, 0) + 1
            today = date.today().isoformat()
            data.setdefault("daily", {})
            data["daily"][today] = data["daily"].get(today, 0) + 1
            data["last_use"] = datetime.now().isoformat(timespec="seconds")
            data.setdefault("first_use", data["last_use"])
            self._save(data)
        except Exception as e:
            log.warning("Stats track failed: %s", e)

    def get(self) -> dict:
        data = self._load()
        cmds = data.get("commands", {})
        top = sorted(cmds.items(), key=lambda kv: kv[1], reverse=True)[:10]
        daily = data.get("daily", {})
        # Last 14 days
        sorted_days = sorted(daily.items())[-14:]
        return {
            "total_commands": data.get("total_commands", 0),
            "total_llm_calls": data.get("total_llm_calls", 0),
            "unique_command_types": len(cmds),
            "top_commands": [{"name": k, "count": v} for k, v in top],
            "daily_activity": [{"date": d, "count": c} for d, c in sorted_days],
            "first_use": data.get("first_use"),
            "last_use": data.get("last_use"),
        }

    def reset(self):
        STATS_FILE.unlink(missing_ok=True)
        self.__init__()


stats_service = StatsService()
