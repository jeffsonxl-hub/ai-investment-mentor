"""SQLite table definitions for AI Investment Mentor.

All CREATE TABLE and CREATE INDEX statements as constants.
Schema version: 1
"""

SCHEMA_VERSION = 1

CREATE_WATCHLIST = """
CREATE TABLE IF NOT EXISTS watchlist (
    stock_code TEXT PRIMARY KEY,
    stock_name TEXT NOT NULL,
    added_date TEXT NOT NULL,
    added_reason TEXT,
    priority TEXT DEFAULT 'medium',
    tags TEXT,
    last_reviewed TEXT,
    notes TEXT,
    active INTEGER DEFAULT 1
)
"""

CREATE_WATCHLIST_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_watchlist_priority ON watchlist(priority, active)",
    "CREATE INDEX IF NOT EXISTS idx_watchlist_last_reviewed ON watchlist(last_reviewed)",
]

CREATE_MARKET_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS market_snapshots (
    date TEXT PRIMARY KEY,
    regime TEXT NOT NULL,
    confidence REAL NOT NULL,
    index_data TEXT NOT NULL,
    leading_sectors TEXT,
    lagging_sectors TEXT,
    northbound_flow REAL,
    shibor_overnight REAL,
    risk_flags TEXT,
    narrative TEXT,
    data_quality TEXT DEFAULT 'full'
)
"""

CREATE_MARKET_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_market_regime ON market_snapshots(regime, date)",
]

CREATE_DECISIONS = """
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    rank INTEGER,
    score REAL,
    score_breakdown TEXT,
    thesis TEXT,
    evidence TEXT,
    risks TEXT,
    confidence REAL,
    suggested_action TEXT,
    deep_dive INTEGER DEFAULT 0,
    learning_point TEXT,
    user_feedback TEXT,
    outcome_notes TEXT,
    created_at TEXT NOT NULL
)
"""

CREATE_DECISIONS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_decisions_date ON decisions(date)",
    "CREATE INDEX IF NOT EXISTS idx_decisions_stock ON decisions(stock_code, date)",
    "CREATE INDEX IF NOT EXISTS idx_decisions_feedback ON decisions(user_feedback, date)",
]

CREATE_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER
)
"""

ALL_TABLES = [
    CREATE_WATCHLIST,
    CREATE_MARKET_SNAPSHOTS,
    CREATE_DECISIONS,
    CREATE_VERSION,
]

ALL_INDEXES = (
    CREATE_WATCHLIST_INDEXES
    + CREATE_MARKET_INDEXES
    + CREATE_DECISIONS_INDEXES
)
