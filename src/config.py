"""Singleton configuration for AI Investment Mentor.

Loads all settings from environment variables with sensible defaults.
Configuration is immutable after loading - call load_config() once at startup.
"""

import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


@dataclass(frozen=True)
class Config:
    """All project configuration. Frozen after initialization."""

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-v4-pro"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2

    # Database
    db_path: str = "data/ai_mentor.db"

    # Data Sources
    tushare_token: str = ""
    akshare_cache_dir: str = "data/cache"
    data_timeout_seconds: int = 30
    data_max_retries: int = 1
    tushare_call_timeout: int = 15
    akshare_call_timeout: int = 30
    akshare_parallel_limit: int = 10
    news_default_limit: int = 20

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/ai_mentor.log"
    log_format: str = "json"

    # Schedule
    daily_analysis_time: str = "08:30"

    def __post_init__(self):
        if not self.llm_api_key:
            raise ConfigError(
                "LLM_API_KEY is required. Set it in .env or environment."
            )


def load_config(env_path: str = ".env") -> Config:
    """Load configuration from environment and optional .env file.

    Returns a frozen Config object. Call once at application startup.
    """
    # Try loading .env file if it exists (optional). Windows may save it
    # as UTF-16 or GBK, so try multiple encodings.
    for enc in ("utf-8", "utf-8-sig", "ascii", "gbk"):
        try:
            with open(env_path, encoding=enc) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    if key and key not in os.environ:
                        os.environ[key] = value
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue

    return Config(
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        llm_model=os.getenv("LLM_MODEL", "deepseek-v4-pro"),
        llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
        llm_max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        db_path=os.getenv("DB_PATH", "data/ai_mentor.db"),
        tushare_token=os.getenv("TUSHARE_TOKEN", ""),
        akshare_cache_dir=os.getenv("AKSHARE_CACHE_DIR", "data/cache"),
        data_timeout_seconds=int(os.getenv("DATA_TIMEOUT_SECONDS", "30")),
        data_max_retries=int(os.getenv("DATA_MAX_RETRIES", "1")),
        tushare_call_timeout=int(os.getenv("TUSHARE_CALL_TIMEOUT", "15")),
        akshare_call_timeout=int(os.getenv("AKSHARE_CALL_TIMEOUT", "30")),
        akshare_parallel_limit=int(os.getenv("AKSHARE_PARALLEL_LIMIT", "10")),
        news_default_limit=int(os.getenv("NEWS_DEFAULT_LIMIT", "20")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/ai_mentor.log"),
        log_format=os.getenv("LOG_FORMAT", "json"),
        daily_analysis_time=os.getenv("DAILY_ANALYSIS_TIME", "08:30"),
    )
