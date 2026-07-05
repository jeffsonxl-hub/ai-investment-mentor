# Memory Design ¡ª AI Investment Mentor

This document defines the memory architecture for V1 of the AI Investment Mentor. It answers: what does the system need to remember, how is it stored, and how do Agents interact with it.

## Design Philosophy

Memory in an AI Agent system serves a different purpose than a traditional application database. An application database stores *facts*. Agent memory stores *context* ¡ª what happened before, what the user cares about, and what the system learned.

Our memory design follows three principles:

1. **Separate storage from intelligence.** Memory lives in a deterministic Component (MemoryRepository). Agents never write SQL or manage connections. They call a clean Python interface and receive structured data back.

2. **Three memory types, three purposes.** Watchlist Memory stores user preferences. Market Memory stores historical snapshots. Decision Memory stores recommendations and outcomes. Each has a distinct schema, access pattern, and retention policy.

3. **Hybrid update strategy.** Some memory is user-managed (watchlist ¡ª human decides). Some is system-managed (market snapshots ¡ª automatic daily). Some is system-written with eventual user feedback (decisions ¡ª AI records, user can later confirm or reject).

## What We Do Not Build in V1

- **RAG (Retrieval-Augmented Generation).** V1 memory is structured SQL queries, not vector search. We do not embed news articles or decision histories for semantic retrieval. This keeps V1 simple and predictable. RAG is a natural V2 addition when we have enough historical data to justify it.
- **LangGraph persistence.** V1 uses a simple Python orchestration layer. LangGraph Checkpointing (Phase 13) will replace or wrap MemoryRepository when we adopt the framework.
- **Real-time memory updates.** Memory is written during the daily analysis batch, not mid-day. The system does not react to intraday events in V1.

## Three Memory Types

### 1. Watchlist Memory

**Purpose**: Store the stocks the user actively tracks, with metadata about why and when they were added.

**Managed by**: Watchlist Agent (reads and proposes changes) + User (approves or rejects changes)

**Schema** (SQLite):
```sql
CREATE TABLE watchlist (
    stock_code TEXT PRIMARY KEY,     -- 6-digit SSE/SZSE code
    stock_name TEXT NOT NULL,         -- Human-readable name
    added_date TEXT NOT NULL,         -- ISO 8601 date
    added_reason TEXT,                -- Why the user or AI added this stock
    priority TEXT DEFAULT 'medium',   -- high | medium | low
    tags TEXT,                        -- JSON array: ["long_term", "swing_trade", "dividend"]
    last_reviewed TEXT,               -- ISO 8601 date of last Advisory mention
    notes TEXT,                       -- User free-text notes (V2)
    active INTEGER DEFAULT 1          -- 0 = soft-deleted (user removed)
);

CREATE INDEX idx_watchlist_priority ON watchlist(priority, active);
CREATE INDEX idx_watchlist_last_reviewed ON watchlist(last_reviewed);
```

**Access patterns**:
- `get_all()` ¡ª Read entire active watchlist (daily, fast)
- `get_by_code(stock_code)` ¡ª Check if a stock is watched
- `add(stock_code, ...)` ¡ª Add a stock (user confirmed)
- `remove(stock_code)` ¡ª Soft-delete (user confirmed)
- `update_priority(stock_code, priority)` ¡ª Change priority
- `touch(stock_code)` ¡ª Update last_reviewed to today

**Retention**: Indefinite. Watchlist is small (10¨C50 stocks). No pruning needed.

**User interaction**: The Watchlist Agent can *recommend* additions or removals, but the `add()` and `remove()` methods require an explicit user confirmation flag. This is the "human-in-the-loop" rule.

---

### 2. Market Memory

**Purpose**: Store daily snapshots of market conditions so the Market Agent can compare today against yesterday (trend detection) and future agents can backtest patterns.

**Managed by**: Market Agent (writes daily) + Advisor Agent (reads for context)

**Schema** (SQLite):
```sql
CREATE TABLE market_snapshots (
    date TEXT PRIMARY KEY,            -- ISO 8601 date
    regime TEXT NOT NULL,             -- risk_on | risk_off | neutral | rotational
    confidence REAL NOT NULL,         -- 0.0 to 1.0
    index_data TEXT NOT NULL,         -- JSON: {sh: {open, high, low, close, volume}, sz: {...}, ...}
    leading_sectors TEXT,             -- JSON array of sector names
    lagging_sectors TEXT,             -- JSON array of sector names
    northbound_flow REAL,             -- Net flow in billion RMB
    shibor_overnight REAL,            -- Overnight SHIBOR rate
    risk_flags TEXT,                  -- JSON array of risk flag strings
    narrative TEXT,                   -- LLM-generated macro summary
    data_quality TEXT DEFAULT 'full'  -- full | degraded | partial
);

CREATE INDEX idx_market_regime ON market_snapshots(regime, date);
```

**Access patterns**:
- `get_latest()` ¡ª Get most recent snapshot (yesterday or today)
- `get_by_date(date)` ¡ª Get a specific day
- `get_range(start_date, end_date)` ¡ª Get a range for trend analysis
- `save(snapshot)` ¡ª Write today assessment
- `get_regime_history(days)` ¡ª Get regime sequence for pattern detection

**Retention**: 2 years (approximately 500 trading days). Beyond that, keep only regime classification and index close for long-term trend reference (aggregated table, V2).

**Data quality flags**: If the Market Agent cannot access all data sources, it writes the best available data with `data_quality = 'degraded'` or `'partial'`. Downstream consumers check this flag before relying on the data for backtesting.

---

### 3. Decision Memory

**Purpose**: Store every recommendation the system makes, the evidence behind it, and (in V2) the outcome ¡ª whether the user acted on it and how it performed.

**Managed by**: Advisor Agent (writes) + Research Agent (reads for pattern learning, V2)

**Schema** (SQLite):
```sql
CREATE TABLE decisions (
    decision_id TEXT PRIMARY KEY,     -- UUID
    date TEXT NOT NULL,               -- ISO 8601 date of recommendation
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    rank INTEGER,                     -- Position in that day candidate list (1 = top pick)
    score REAL,                       -- Composite score 0¨C10
    score_breakdown TEXT,             -- JSON: {fundamental: 7.0, technical: 8.5, ...}
    thesis TEXT,                      -- LLM-generated investment thesis
    evidence TEXT,                    -- JSON array of evidence items with source attribution
    risks TEXT,                       -- JSON array of risk descriptions
    confidence REAL,                  -- 0.0 to 1.0
    suggested_action TEXT,            -- review | watch | avoid
    deep_dive INTEGER DEFAULT 0,      -- 1 = this was the deep-dive pick
    learning_point TEXT,              -- The educational takeaway from this recommendation
    user_feedback TEXT,               -- NULL = no feedback yet | confirmed | rejected | acted_on (V2)
    outcome_notes TEXT,               -- User or system notes on what happened (V2)
    created_at TEXT NOT NULL          -- Timestamp
);

CREATE INDEX idx_decisions_date ON decisions(date);
CREATE INDEX idx_decisions_stock ON decisions(stock_code, date);
CREATE INDEX idx_decisions_feedback ON decisions(user_feedback, date);
```

**Access patterns**:
- `save_decision(decision)` ¡ª Write a new recommendation
- `get_by_date(date)` ¡ª Get all recommendations for a day
- `get_by_stock(stock_code, limit)` ¡ª Get recommendation history for a stock
- `get_recent_decisions(days)` ¡ª Get decisions within N days (for duplicate detection)
- `get_rejected_stocks(days)` ¡ª Get stocks the user rejected recently (for filtering)
- `update_feedback(decision_id, feedback)` ¡ª Record user feedback (V2)

**Retention**: Indefinite. Decision records are the most valuable data for future learning. Even rejected recommendations teach the system about user preferences.

**Duplicate prevention**: Before presenting a candidate, the Advisor checks Decision Memory for recent mentions. If the same stock was recommended in the last 5 trading days with the same thesis, it is flagged as "previously reviewed" rather than re-presented as new.

---

## How Agents Interact with Memory

This is the critical design rule:

**Agents never access the database directly. They call MemoryRepository methods.**

```
©°©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©´     read/write     ©°©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©´     SQL     ©°©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©´
©¦   Agent     ©¦ ©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤? ©¦ MemoryRepository ©¦ ©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤? ©¦  SQLite  ©¦
©¦  (Python)   ©¦ ?©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤ ©¦   (Python class)  ©¦ ?©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤ ©¦   (.db)  ©¦
©¸©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¼   structured data  ©¸©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¼   rows      ©¸©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¼
```

Why this indirection matters:
- **Testability**: You can mock MemoryRepository in Agent unit tests ¡ª no real database needed
- **Swappability**: If we move from SQLite to PostgreSQL in V2, only MemoryRepository changes, not the Agents
- **Safety**: MemoryRepository enforces schema constraints. An Agent cannot accidentally write malformed data
- **Auditability**: All memory access goes through one class. Log it, time it, trace it

## SQLite Selection Rationale

| Criterion | SQLite | PostgreSQL | JSON files |
|---|---|---|---|
| Setup complexity | Zero (built into Python) | Requires server + config | Zero |
| Query power | Full SQL | Full SQL | Manual grep |
| Concurrent access | Single-writer (fine for 1 user) | Multi-user | N/A |
| Data integrity | ACID | ACID | No guarantees |
| Backup | Copy one file | pg_dump | Copy files |
| V2 migration path | Can migrate to PostgreSQL | Already there | Painful rewrite |

SQLite is the right choice for V1. It has zero operational overhead, ships inside Python, and handles our data volumes (thousands of rows, not millions) effortlessly. If we ever need multi-user or high-frequency writes, migrating to PostgreSQL is straightforward because we abstract the storage behind MemoryRepository.

## Migration Strategy

V1 starts with a fresh SQLite database. We do not need migration tooling yet because:
1. There is no production data to preserve
2. Schema changes during development can be handled by deleting and recreating the database
3. When we reach Phase 7 (Project Standards), we will add Alembic or a simple migration script pattern

The database file is created on first access with `CREATE TABLE IF NOT EXISTS` statements. No manual setup step is required.

## Edge Cases & Error Handling

| Scenario | Behavior |
|---|---|
| Database file does not exist | MemoryRepository creates it on first `initialize()` call |
| Database file is corrupted | Detect on open, rename to `.db.bak`, create fresh, log warning |
| Write during read (concurrent access) | SQLite handles this with WAL mode. Single-user V1 makes this unlikely |
| Disk full | `sqlite3.OperationalError` ¡ú MemoryRepository raises `MemoryError` ¡ú Agent degrades gracefully |
| Schema mismatch (V1 code against V2 schema) | Version table check on `initialize()`. If version mismatch, raise clear error with migration instructions |
