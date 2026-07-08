# DEVELOPMENT.md -- AI Investment Mentor

Engineering standards for every contributor (human and Codex). When in doubt, this document is the tiebreaker.

---

## Type Hints

All public function signatures must be typed. This is non-negotiable at boundaries between packages (e.g., `src/tools/` calling `src/data/`). Internal helpers and private methods may relax when the type is obvious from context.

```python
# Required: public interfaces
def get_index_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    ...

# Acceptable: trivial private helper
def _validate_nonempty(self, value):
    ...
```

Rationale: Agents call tools, tools call components -- a type error at a boundary surfaces three layers away. The type system is the only automated check between an LLM's output and your database.

---

## Docstrings

Google-style docstrings for all public interfaces. Args/Returns/Raises required. No docstrings on trivial private helpers -- if the function name and types tell the whole story, a docstring is noise.

```python
def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index for a price series.

    Args:
        prices: Series of closing prices.
        period: Lookback window. Defaults to 14.

    Returns:
        Series of RSI values (0.0-100.0), same index as input.

    Raises:
        ValueError: If period > len(prices) or period < 1.
    """
```

---

## Imports

Three blocks, separated by blank lines, in this order:

1. Standard library
2. Third-party packages
3. Local (`src.` prefix)

Absolute imports only. No relative `..` imports across package boundaries. Within a single package, `from .module import X` is fine.

```python
# Correct
import asyncio
from datetime import date

import pandas as pd
from pydantic import BaseModel

from src.data.provider import DataProvider
from src.tools.registry import ToolRegistry

# Wrong -- relative across packages
from ..data.provider import DataProvider
```

---

## Line Length

110 characters. Prompt strings in agent code are naturally long, and 88 (the `black` default) forces awkward line breaks in descriptions the LLM reads at runtime.

---

## Linting

`ruff` for both linting and formatting. One tool, zero config for 90% of cases.

```bash
# Check only (CI)
ruff check src/ tests/

# Auto-fix
ruff check --fix src/ tests/

# Format
ruff format src/ tests/
```

Configuration in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]

[tool.ruff.format]
quote-style = "double"
```

---

## Type Checking

`mypy` runs on CI only (not blocking for V1). Configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
strict = false
ignore_missing_imports = true
```

---

## Testing

### Structure

```
tests/
  unit/           # Mirrors src/ -- one test file per source module
  integration/    # External dependencies: LLM calls, AkShare, SQLite
  prompts/        # Prompt output schema validation
```

### Standards

- Use `pytest` with plain `assert` -- no unittest.TestCase.
- Test file naming: `test_<module>.py`.
- Integration tests use `@pytest.mark.integration` decorator.
- Prompt tests validate that prompt output parses against its Pydantic model. They do not test LLM "correctness" -- only structural validity.

### Running

```bash
# All tests
pytest

# Unit tests only (fast, no network)
pytest tests/unit/ -q

# Integration tests (requires .env tokens)
pytest tests/integration/ -v

# Prompt tests
pytest tests/prompts/ -v
```

---

## Pre-Commit Checklist

Before any commit:

```bash
pip install -r requirements.txt
ruff check src/ tests/
pytest tests/unit/ -q
```

If a dependency was added: update `requirements.txt`. If the change touches prompt files: also run `pytest tests/prompts/`.

---

## Editor

`.editorconfig` at the project root ensures consistent whitespace across editors:

```ini
root = true

[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.md]
trim_trailing_whitespace = false
```