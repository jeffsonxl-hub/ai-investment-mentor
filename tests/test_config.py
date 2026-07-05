"""Tests for ConfigLoader component."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure a clean environment for each test."""
    for key in ("LLM_API_KEY", "LLM_MODEL", "LLM_BASE_URL",
                "DB_PATH", "LOG_LEVEL", "LOG_FORMAT"):
        monkeypatch.delenv(key, raising=False)


def test_config_loads_defaults(monkeypatch):
    """Config should load with sensible defaults when no env vars are set."""
    monkeypatch.setenv("LLM_API_KEY", "sk-test-placeholder")

    from config import load_config
    cfg = load_config(env_path=".env.nonexistent")

    assert cfg.llm_base_url == "https://api.deepseek.com/v1"
    assert cfg.llm_model == "deepseek-v4-pro"
    assert cfg.llm_timeout_seconds == 60
    assert cfg.llm_max_retries == 2
    assert cfg.db_path == "data/ai_mentor.db"
    assert cfg.log_level == "INFO"
    assert cfg.log_format == "json"
    assert cfg.data_timeout_seconds == 30
    assert cfg.data_max_retries == 1
    assert cfg.daily_analysis_time == "08:30"


def test_config_from_environment(monkeypatch):
    """Config should read values from environment variables."""
    monkeypatch.setenv("LLM_API_KEY", "test-key-123")
    monkeypatch.setenv("LLM_MODEL", "deepseek-v4-pro")
    monkeypatch.setenv("DB_PATH", "data/test.db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    from config import load_config
    cfg = load_config(env_path=".env.nonexistent")

    assert cfg.llm_api_key == "test-key-123"
    assert cfg.llm_model == "deepseek-v4-pro"
    assert cfg.db_path == "data/test.db"
    assert cfg.log_level == "DEBUG"


def test_config_missing_api_key_raises(monkeypatch):
    """Config should raise ConfigError if LLM_API_KEY is not set."""
    # Ensure LLM_API_KEY is not in the environment
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    from config import load_config, ConfigError

    with pytest.raises(ConfigError, match="LLM_API_KEY"):
        load_config(env_path=".env.nonexistent")

