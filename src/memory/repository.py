"""MemoryRepository -- deterministic SQLite persistence for all three memory types.

This is a Component, not an Agent. No LLM, no reasoning, no business logic.
"""

import json
import sqlite3
from datetime import datetime, timezone

from .exceptions import MemoryRepositoryError
from .schema import ALL_INDEXES, ALL_TABLES, SCHEMA_VERSION


class MemoryRepository:
    """Single point of contact between Agent Layer and SQLite database."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._conn = None
        self._initialized = False

    def _get_conn(self) -> sqlite3.Connection:
        """Lazy connection. Auto-initializes if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
        if not self._initialized:
            self._initialize_schema()
        return self._conn

    def _initialize_schema(self) -> None:
        """Create tables and indexes. Idempotent."""
        try:
            for stmt in ALL_TABLES:
                self._conn.execute(stmt)
            for stmt in ALL_INDEXES:
                self._conn.execute(stmt)
            row = self._conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()
            if row[0] == 0:
                self._conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SCHEMA_VERSION,),
                )
            self._conn.commit()
            self._initialized = True
        except sqlite3.Error as e:
            raise MemoryRepositoryError(f"Schema initialization failed: {e}")

    def initialize(self) -> None:
        """Public initializer. Idempotent."""
        self._get_conn()

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._initialized = False

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Run SQL, wrapping errors in MemoryRepositoryError."""
        try:
            return self._get_conn().execute(sql, params)
        except sqlite3.Error as e:
            raise MemoryRepositoryError(f"Database error: {e}")

    # -- Watchlist ------------------------------------------------------------

    def get_watchlist(self) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM watchlist WHERE active = 1 ORDER BY priority, stock_code"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_watchlist_entry(self, stock_code: str) -> dict | None:
        row = self._execute(
            "SELECT * FROM watchlist WHERE stock_code = ? AND active = 1",
            (stock_code,),
        ).fetchone()
        return dict(row) if row else None

    def add_to_watchlist(
        self,
        stock_code: str,
        stock_name: str,
        reason: str,
        priority: str = "medium",
    ) -> None:
        existing = self._execute(
            "SELECT 1 FROM watchlist WHERE stock_code = ? AND active = 1",
            (stock_code,),
        ).fetchone()
        if existing:
            raise ValueError(f"Stock {stock_code} is already in the watchlist")
        self._execute(
            "INSERT INTO watchlist (stock_code, stock_name, added_date, added_reason, priority) "
            "VALUES (?, ?, ?, ?, ?)",
            (stock_code, stock_name, self._now_date(), reason, priority),
        )
        self._get_conn().commit()

    def remove_from_watchlist(self, stock_code: str) -> None:
        self._execute(
            "UPDATE watchlist SET active = 0 WHERE stock_code = ?",
            (stock_code,),
        )
        self._get_conn().commit()

    def update_watchlist_priority(self, stock_code: str, priority: str) -> None:
        row = self._execute(
            "SELECT 1 FROM watchlist WHERE stock_code = ? AND active = 1",
            (stock_code,),
        ).fetchone()
        if not row:
            raise ValueError(f"Stock {stock_code} is not in the watchlist")
        self._execute(
            "UPDATE watchlist SET priority = ? WHERE stock_code = ?",
            (priority, stock_code),
        )
        self._get_conn().commit()

    def touch_watchlist_entry(self, stock_code: str) -> None:
        self._execute(
            "UPDATE watchlist SET last_reviewed = ? WHERE stock_code = ?",
            (self._now_date(), stock_code),
        )
        self._get_conn().commit()

    # -- Market Snapshots -----------------------------------------------------

    def get_latest_market_snapshot(self) -> dict | None:
        row = self._execute("SELECT * FROM market_snapshots ORDER BY date DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def get_market_snapshot(self, date: str) -> dict | None:
        row = self._execute("SELECT * FROM market_snapshots WHERE date = ?", (date,)).fetchone()
        return dict(row) if row else None

    def get_market_snapshot_range(self, start_date: str, end_date: str) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM market_snapshots WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (start_date, end_date),
        ).fetchall()
        return [dict(r) for r in rows]

    def save_market_snapshot(self, snapshot: dict) -> None:
        self._execute(
            "INSERT OR REPLACE INTO market_snapshots "
            "(date, regime, confidence, index_data, leading_sectors, lagging_sectors, "
            " northbound_flow, shibor_overnight, risk_flags, narrative, data_quality) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                snapshot["date"],
                snapshot["regime"],
                snapshot["confidence"],
                json.dumps(snapshot.get("index_data", {})),
                json.dumps(snapshot.get("leading_sectors", [])),
                json.dumps(snapshot.get("lagging_sectors", [])),
                snapshot.get("northbound_flow"),
                snapshot.get("shibor_overnight"),
                json.dumps(snapshot.get("risk_flags", [])),
                snapshot.get("narrative", ""),
                snapshot.get("data_quality", "full"),
            ),
        )
        self._get_conn().commit()

    def get_regime_history(self, days: int = 20) -> list[dict]:
        rows = self._execute(
            "SELECT date, regime FROM market_snapshots ORDER BY date DESC LIMIT ?",
            (days,),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- Decisions ------------------------------------------------------------

    def save_decision(self, decision: dict) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._execute(
            "INSERT INTO decisions "
            "(decision_id, date, stock_code, stock_name, rank, score, score_breakdown, "
            " thesis, evidence, risks, confidence, suggested_action, "
            " deep_dive, learning_point, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                decision["decision_id"],
                decision["date"],
                decision["stock_code"],
                decision["stock_name"],
                decision.get("rank"),
                decision.get("score"),
                json.dumps(decision.get("score_breakdown", {})),
                decision.get("thesis", ""),
                json.dumps(decision.get("evidence", [])),
                json.dumps(decision.get("risks", [])),
                decision.get("confidence"),
                decision.get("suggested_action", ""),
                1 if decision.get("deep_dive") else 0,
                decision.get("learning_point", ""),
                decision.get("created_at", now),
            ),
        )
        self._get_conn().commit()

    def get_decisions_by_date(self, date: str) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM decisions WHERE date = ? ORDER BY rank",
            (date,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_decisions_by_stock(self, stock_code: str, limit: int = 20) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM decisions WHERE stock_code = ? ORDER BY date DESC LIMIT ?",
            (stock_code, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_decisions(self, days: int = 5) -> list[dict]:
        rows = self._execute(
            "SELECT * FROM decisions WHERE date >= ? ORDER BY date DESC",
            (self._now_date(offset_days=-days),),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_rejected_stocks(self, days: int = 20) -> list[str]:
        rows = self._execute(
            "SELECT stock_code FROM decisions WHERE user_feedback = 'rejected' AND date >= ?",
            (self._now_date(offset_days=-days),),
        ).fetchall()
        return [r["stock_code"] for r in rows]

    def update_decision_feedback(self, decision_id: str, feedback: str) -> None:
        self._execute(
            "UPDATE decisions SET user_feedback = ? WHERE decision_id = ?",
            (feedback, decision_id),
        )
        self._get_conn().commit()

    # -- Data Source Status ---------------------------------------------------

    def save_source_status(
        self,
        source: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Record a data source operational status for today."""
        self._execute(
            "INSERT INTO data_source_status (date, source, status, error_message, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (self._now_date(), source, status, error_message, self._now_iso()),
        )
        self._get_conn().commit()

    def get_source_status(self, date: str) -> list[dict]:
        """Return all source status records for a given date."""
        rows = self._execute(
            "SELECT * FROM data_source_status WHERE date = ? ORDER BY created_at",
            (date,),
        ).fetchall()
        return [dict(r) for r in rows]

    # -- Helpers --------------------------------------------------------------

    @staticmethod
    def _now_date(offset_days: int = 0) -> str:
        """Return today's date in ISO 8601 format (YYYY-MM-DD), optionally offset by N days."""
        from datetime import date, timedelta

        return (date.today() + timedelta(days=offset_days)).isoformat()

    @staticmethod
    def _now_iso() -> str:
        """Return current UTC datetime in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()
