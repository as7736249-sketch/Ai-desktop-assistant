"""Central logger factory (colored console + rotating file)."""
import logging
import sys
from logging.handlers import RotatingFileHandler

import colorlog

from app.core.config import settings

_CONFIGURED: bool = False


def _configure_root_logger() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)

    # Prevent duplicate handlers (e.g., under uvicorn --reload)
    for h in list(root.handlers):
        root.removeHandler(h)

    # Colored console
    console_fmt = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        log_colors={
            "DEBUG": "cyan", "INFO": "green", "WARNING": "yellow",
            "ERROR": "red", "CRITICAL": "bold_red",
        },
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(console_fmt)
    root.addHandler(ch)

    # Rotating file
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    try:
        fh = RotatingFileHandler(
            filename=settings.logs_dir / "assistant.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        fh.setFormatter(file_fmt)
        root.addHandler(fh)
    except Exception as e:
        # Never crash the app because of logging
        print(f"[logger] Could not open log file: {e}")

    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root_logger()
    return logging.getLogger(name)
