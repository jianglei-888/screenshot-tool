"""Logging utility for the screenshot tool.

Provides a single get_logger() entry point that configures:
- Console output (stderr)
- File output to %APPDATA%/screenshot-tool/log.txt (auto-created)

Log level can be overridden via the LOG_LEVEL environment variable
(DEBUG / INFO / WARNING / ERROR; default INFO).
"""
import logging
import os
from pathlib import Path

APP_NAME = "screenshot-tool"
APP_LOGGER_NAME = "screenshot_tool"

LOG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
LOG_FILE = LOG_DIR / "log.txt"

LOG_FORMAT = "%(asctime)s - %(levelname)-8s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}

LOG_LEVEL = _LEVEL_MAP.get(
    os.environ.get("LOG_LEVEL", "INFO").upper(),
    logging.INFO,
)

_initialized = False


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _build_handlers() -> list[logging.Handler]:
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(LOG_LEVEL)
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(formatter)

    return [console, file_handler]


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a configured logger.

    The first call initialises the application logger (handlers attached once);
    subsequent calls return child loggers when `name` is provided.

    Args:
        name: Logger suffix. Pass `__name__` from the calling module so
              the source module appears in log records.

    Usage:
        from src.logger import get_logger
        log = get_logger(__name__)
        log.info("Application started")
    """
    global _initialized

    if not _initialized:
        _ensure_log_dir()
        app_logger = logging.getLogger(APP_LOGGER_NAME)
        app_logger.setLevel(LOG_LEVEL)
        if not app_logger.handlers:
            for handler in _build_handlers():
                app_logger.addHandler(handler)
        app_logger.propagate = False
        _initialized = True

    if name is None:
        return logging.getLogger(APP_LOGGER_NAME)

    # Strip "src." prefix so child loggers read as e.g. "screenshot_tool.main"
    suffix = name[4:] if name.startswith("src.") else name
    return logging.getLogger(f"{APP_LOGGER_NAME}.{suffix}")
