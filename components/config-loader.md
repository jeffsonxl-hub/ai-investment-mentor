# ConfigLoader

## Name
ConfigLoader

## Purpose
Loads and validates all project configuration from environment variables and optional configuration files. Provides a single, typed access point for settings used by all Agents and Components.

## Responsibilities

- Load environment variables from `.env` file (via python-dotenv)
- Provide typed accessors for all configuration values with sensible defaults
- Validate required values on initialization (fail fast if missing)
- Expose a single `Config` object that the rest of the system imports
- Never expose secrets in logs or error messages

This component does NOT:
- Perform any reasoning or decision-making
- Call an LLM
- Modify configuration at runtime (read-only after initialization)

## Public Interface

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    """All project configuration. Frozen after initialization ！ no runtime mutation."""

    # LLM
    llm_api_key: str
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2

    # Database
    db_path: str = "data/ai_mentor.db"

    # Data Sources
    akshare_cache_dir: str = "data/cache"
    data_timeout_seconds: int = 30
    data_max_retries: int = 1

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/ai_mentor.log"
    log_format: str = "json"  # json | text

    # Schedule
    daily_analysis_time: str = "08:30"  # 24-hour format, local timezone

    # Scoring
    scoring_weights_risk_on: dict = None   # Falls back to defaults
    scoring_weights_risk_off: dict = None
    scoring_weights_normal: dict = None

    def __post_init__(self):
        """Validate required fields on initialization."""
        if not self.llm_api_key:
            raise ConfigError("LLM_API_KEY is required. Set it in .env or environment.")


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


def load_config(env_path: str = ".env") -> Config:
    """Load configuration from environment and .env file.
    Returns a frozen Config object. Call once at application startup."""
```

### Environment Variables

All configuration maps to environment variables documented in `.env.example`:

```bash
# LLM
LLM_API_KEY=           # Required: OpenAI-compatible API key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=2

# Database
DB_PATH=data/ai_mentor.db

# Data Sources
AKSHARE_CACHE_DIR=data/cache
DATA_TIMEOUT_SECONDS=30
DATA_MAX_RETRIES=1

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ai_mentor.log
LOG_FORMAT=json

# Schedule
DAILY_ANALYSIS_TIME=08:30
```

## Dependencies

- `python-dotenv` ！ load `.env` file
- `dataclasses` ！ Python standard library
- No other external dependencies

## Consumers

| Consumer | Config Values Used |
|---|---|
| MemoryRepository | `db_path` |
| All Agents | `llm_*` settings |
| Market Agent / Research Agent | `data_*` settings |
| Advisor Agent | `scoring_weights_*`, `daily_analysis_time` |
| Logger | `log_*` settings |

## Constraints

- **Immutable after load.** No Agent can change configuration at runtime. This prevents bugs where one Agent's config change breaks another
- **Secrets never logged.** `llm_api_key` must be redacted in all log output
- **Fail fast on missing required values.** Do not start the application with a missing API key ！ raise `ConfigError` immediately
- **All values have defaults except `llm_api_key`.** The system should be runnable with minimal setup
- **No LLM access.** This is a Component, not an Agent

## Future Evolution

- **V2: Configuration file support.** Allow `config.yaml` as an alternative to environment variables for complex settings (scoring weights, agent-specific thresholds)
- **V2: Hot reload.** Allow non-critical settings to be updated without restart (log level, scoring weights)
- **V2: Profile support.** Allow multiple config profiles (conservative/aggressive) selectable at startup
