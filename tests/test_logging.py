"""Tests for logging setup."""

import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_setup_logging_writes_json_line():
    """setup_logging should produce valid JSON-line output."""
    from logging_config import setup_logging

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name

    try:
        logger = setup_logging(log_file=log_path, log_format="json")
        logger.info("Test message", extra={"step": "test"})

        # Close handlers so Windows can unlink the file
        for handler in logging.getLogger().handlers[:]:
            handler.close()
            logging.getLogger().removeHandler(handler)

        with open(log_path) as f:
            lines = f.readlines()

        assert len(lines) >= 1
        record = json.loads(lines[0])
        assert record["message"] == "Test message"
        assert record["step"] == "test"
        assert "timestamp" in record
        assert record["level"] == "INFO"
    finally:
        if os.path.exists(log_path):
            os.unlink(log_path)


def test_setup_logging_text_format():
    """setup_logging should support plain text format."""
    from logging_config import setup_logging

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_path = f.name

    try:
        logger = setup_logging(log_file=log_path, log_format="text")
        logger.warning("Something happened")

        for handler in logging.getLogger().handlers[:]:
            handler.close()
            logging.getLogger().removeHandler(handler)

        with open(log_path) as f:
            content = f.read()

        assert "Something happened" in content
        assert "WARNING" in content
    finally:
        if os.path.exists(log_path):
            os.unlink(log_path)
