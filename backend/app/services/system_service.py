"""
System info service — battery, CPU, memory, screenshot.
Uses only standard library + optional psutil.
"""
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger

log = get_logger(__name__)


class SystemService:
    def battery(self) -> str:
        try:
            import psutil
            bat = psutil.sensors_battery()
            if bat is None:
                return "No battery detected (probably a desktop)."
            pct = int(bat.percent)
            plugged = "plugged in" if bat.power_plugged else "on battery"
            return f"Battery is at {pct} percent, {plugged}."
        except ImportError:
            return "Battery info unavailable (psutil not installed)."
        except Exception as e:
            log.warning("Battery check failed: %s", e)
            return "Could not read battery status."

    def cpu(self) -> str:
        try:
            import psutil
            pct = psutil.cpu_percent(interval=0.5)
            cores = psutil.cpu_count(logical=True)
            return f"CPU usage is {pct:.0f} percent across {cores} logical cores."
        except ImportError:
            return "CPU info unavailable (psutil not installed)."
        except Exception as e:
            log.warning("CPU check failed: %s", e)
            return "Could not read CPU status."

    def memory(self) -> str:
        try:
            import psutil
            m = psutil.virtual_memory()
            return (
                f"Memory: {m.percent:.0f} percent used. "
                f"{m.used // (1024**3):.1f} GB of {m.total // (1024**3):.1f} GB."
            )
        except ImportError:
            return "Memory info unavailable (psutil not installed)."
        except Exception as e:
            log.warning("Memory check failed: %s", e)
            return "Could not read memory status."

    def disk(self) -> str:
        try:
            total, used, free = shutil.disk_usage(os.path.expanduser("~"))
            gb = 1024 ** 3
            pct = (used / total) * 100
            return (
                f"Disk: {pct:.0f} percent used. "
                f"{used // gb} GB of {total // gb} GB, "
                f"{free // gb} GB free."
            )
        except Exception as e:
            log.warning("Disk check failed: %s", e)
            return "Could not read disk status."

    def screenshot(self, save_dir: Optional[Path] = None) -> str:
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            save_dir = save_dir or Path.home() / "Pictures"
            save_dir.mkdir(parents=True, exist_ok=True)
            fname = f"jarvis_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = save_dir / fname
            img.save(path)
            return f"Screenshot saved to {path}."
        except ImportError:
            return "Screenshot needs Pillow: pip install Pillow"
        except Exception as e:
            log.warning("Screenshot failed: %s", e)
            return "Could not take screenshot."

    def os_info(self) -> str:
        try:
            return (
                f"Running {platform.system()} {platform.release()} "
                f"on {platform.machine()}. "
                f"Python {platform.python_version()}."
            )
        except Exception:
            return "Could not read OS info."


system_service = SystemService()
