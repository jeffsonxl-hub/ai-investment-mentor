# MemoryRepository

## Name
MemoryRepository

## Purpose
Provides a deterministic persistence layer for all three memory types (Watchlist, Market, Decision) using SQLite. It is the single point of contact between the Agent Layer and the database.

## Responsibilities

- Create and manage the SQLite database file on first access
- Provide typed read/write methods for Watchlist Memory
- Provide typed read/write methods for Market Memory
- Provide typed read/write methods for Decision Memory
- Handle database initialization (CREATE TABLE IF NOT EXISTS, WAL mode, version check)
- Handle connection lifecycle (open, close, connection pooling for single-user access)
- Return structured data (dicts, lists) ！ never raw SQL rows or cursors
- Log all write operations for audit trail

This component does NOT:
- Perform any reasoning or decision-making
- Call an LLM
- Contain business logic (it does not know what "watchlist priority" means ！ it just reads and writes)
- Validate data beyond schema constraints (the calling Agent is responsible for data correctness)

## Public Interface

### Lifecycle

```python
class MemoryRepository:
    def __init__(self, db_path: str) -> None:
        """Initialize with path to SQLite database file. Does NOT open a connection."""

    def initialize(self) -> None:
        """Create tables and indexes if they do not exist. Enable WAL mode.
        Must be called once before any read/write operations."""

    def close(self) -> None:
        """Close all connections cleanly."""
```

### Watchlist Methods

```python
    def get_watchlist(self) -> list[dict]:
        """Return all active watchlist entries as list of dicts.
        Each dict: {stock_code, stock_name, added_date, added_reason, priority, tags, last_reviewed, notes}"""

    def get_watchlist_entry(self, stock_code: str) -> dict | None:
        """Return a single watchlist entry by stock code, or None if not found."""

    def add_to_watchlist(self, stock_code: str, stock_name: str,
                         reason: str, priority: str = "medium") -> None:
        """Add a stock to the watchlist. Raises ValueError if already present."""

    def remove_from_watchlist(self, stock_code: str) -> None:
        """Soft-delete a stock (sets active=0). No error if not found."""

    def update_watchlist_priority(self, stock_code: str, priority: str) -> None:
        """Change priority. Raises ValueError if stock not in watchlist."""

    def touch_watchlist_entry(self, stock_code: str) -> None:
        """Update last_reviewed to current date."""
```

### Market Memory Methods

```python
    def get_latest_market_snapshot(self) -> dict | None:
        """Return the most recent market snapshot, or None if table is empty."""

    def get_market_snapshot(self, date: str) -> dict | None:
        """Return market snapshot for a specific date, or None."""

    def get_market_snapshot_range(self, start_date: str, end_date: str) -> list[dict]:
        """Return snapshots within date range, ordered by date ascending."""

    def save_market_snapshot(self, snapshot: dict) -> None:
        """Insert or replace a market snapshot. date is the primary key."""

    def get_regime_history(self, days: int = 20) -> list[dict]:
        """Return last N days of regime + date, ordered by date descending."""
```

### Decision Memory Methods

```python
    def save_decision(self, decision: dict) -> None:
        """Insert a new decision record. decision_id must be unique."""

    def get_decisions_by_date(self, date: str) -> list[dict]:
        """Return all decisions for a given date."""

    def get_decisions_by_stock(self, stock_code: str, limit: int = 20) -> list[dict]:
        """Return recent decisions for a specific stock, most recent first."""

    def get_recent_decisions(self, days: int = 5) -> list[dict]:
        """Return all decisions from the last N days."""

    def get_rejected_stocks(self, days: int = 20) -> list[str]:
        """Return stock codes the user rejected in the last N days."""

    def update_decision_feedback(self, decision_id: str, feedback: str) -> None:
        """Record user feedback. V2 feature ！ no-op in V1."""
```

## Dependencies

- **Python standard library**: `sqlite3` ！ zero external dependencies
- **No network access required** ！ SQLite is an embedded file database
- **File system**: Read/write access to the directory containing the database file

## Consumers

| Consumer | Methods Used |
|---|---|
| Market Agent | `get_latest_market_snapshot`, `save_market_snapshot`, `get_regime_history` |
| Research Agent | `get_recent_decisions` (V2: event-to-price correlation) |
| Watchlist Agent | All watchlist methods, `get_market_snapshot` (for alert context) |
| Advisor Agent | `get_recent_decisions`, `get_rejected_stocks`, `save_decision`, `update_decision_feedback` |

## Constraints

- **No LLM access.** This is a Component, not an Agent
- **No business logic.** It does not know what a "good" watchlist entry looks like
- **No cross-table logic.** If an operation requires data from two memory types, the calling Agent makes two separate calls
- **Connection safety.** All public methods must handle the case where `initialize()` has not been called by auto-initializing
- **Thread safety.** V1 is single-threaded. If multi-threading is added later, wrap write operations in a mutex
- **Error propagation.** All SQLite errors are wrapped in a custom `MemoryRepositoryError` exception to decouple callers from the storage implementation

## Future Evolution

- **V2: Async support.** Wrap methods with `asyncio` or switch to `aiosqlite` for non-blocking I/O when the Agent Layer becomes async (LangGraph phase)
- **V2: Migration framework.** Add schema version tracking and migration scripts when the schema stabilizes
- **V2: Read replicas.** If we switch to PostgreSQL for multi-user, add read/write split configuration
- **V2: Write-ahead audit log.** Append-only log of all write operations for full replay capability
