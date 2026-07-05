"""Structured logging for AI Investment Mentor.

Provides JSON-line logging for machine-parseable output and
plain-text logging for development.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Attach any extra fields passed via the `extra` kwarg
        for key in dir(record):
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno",
                "lineno", "module", "msecs", "message", "msg",
                "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
            }:
                val = getattr(record, key, None)
                if val is not None and not key.startswith("_"):
                    payload[key] = val
        return json.dumps(payload, default=str)


def setup_logging(
    log_file: str = "logs/ai_mentor.log",
    log_format: str = "json",
) -> logging.Logger:
    """Configure and return the root logger.

    Args:
        log_file: Path to log file.
        log_format: "json" or "text".

    Returns:
        Configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)

    if log_format == "json":
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
        )

    logger.addHandler(file_handler)

    # Console handler (info and above)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(
        logging.Formatter("[%(levelname)s] %(message)s")
    )
    logger.addHandler(console)

    return logger
