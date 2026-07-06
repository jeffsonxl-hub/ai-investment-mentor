"""Tests for MemoryRepository component."""

import os
import sys
import sqlite3
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))



def test_watchlist_crud(tmp_path):
    """Watchlist: add, get, get_all, update priority, touch, remove."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))

    # Add entries
    repo.add_to_watchlist("600519", "Kweichow Moutai", "User request", "high")
    repo.add_to_watchlist("002415", "Hikvision", "AI theme", "medium")

    # Get all
    wl = repo.get_watchlist()
    assert len(wl) == 2

    # Get single
    entry = repo.get_watchlist_entry("600519")
    assert entry["stock_name"] == "Kweichow Moutai"
    assert entry["priority"] == "high"

    # Nonexistent
    assert repo.get_watchlist_entry("999999") is None

    # Update priority
    repo.update_watchlist_priority("600519", "low")
    assert repo.get_watchlist_entry("600519")["priority"] == "low"

    # Touch
    repo.touch_watchlist_entry("600519")
    assert repo.get_watchlist_entry("600519")["last_reviewed"] is not None

    # Remove (soft delete)
    repo.remove_from_watchlist("600519")
    assert repo.get_watchlist_entry("600519") is None
    assert len(repo.get_watchlist()) == 1

    repo.close()


def test_watchlist_duplicate_raises(tmp_path):
    """Adding the same stock twice should raise ValueError."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))
    repo.add_to_watchlist("600519", "Moutai", "test", "medium")
    with pytest.raises(ValueError, match="already in"):
        repo.add_to_watchlist("600519", "Moutai", "again", "high")
    repo.close()


def test_watchlist_update_nonexistent_raises(tmp_path):
    """Updating priority for nonexistent stock should raise ValueError."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))
    with pytest.raises(ValueError, match="not in"):
        repo.update_watchlist_priority("999999", "high")
    repo.close()


def test_watchlist_remove_idempotent(tmp_path):
    """Removing the same stock twice should not error."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))
    repo.add_to_watchlist("600519", "Moutai", "test", "medium")
    repo.remove_from_watchlist("600519")
    repo.remove_from_watchlist("600519")  # No error
    repo.close()


def test_market_snapshot_crud(tmp_path):
    """Market: save, get, get_latest, get_range, regime history."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))

    # Empty state
    assert repo.get_latest_market_snapshot() is None

    # Save
    snap = {
        "date": "2026-07-06",
        "regime": "risk_on",
        "confidence": 0.85,
        "index_data": {"sh": 3500},
        "data_quality": "full",
    }
    repo.save_market_snapshot(snap)

    # Get
    fetched = repo.get_market_snapshot("2026-07-06")
    assert fetched["regime"] == "risk_on"
    assert fetched["confidence"] == 0.85

    # Get latest
    latest = repo.get_latest_market_snapshot()
    assert latest["date"] == "2026-07-06"

    # Get range
    snap2 = {
        "date": "2026-07-07",
        "regime": "neutral",
        "confidence": 0.60,
        "index_data": {"sh": 3480},
        "data_quality": "full",
    }
    repo.save_market_snapshot(snap2)
    rng = repo.get_market_snapshot_range("2026-07-06", "2026-07-07")
    assert len(rng) == 2

    # Regime history
    hist = repo.get_regime_history(5)
    assert len(hist) == 2
    assert hist[0]["date"] == "2026-07-07"

    repo.close()


def test_decision_crud(tmp_path):
    """Decisions: save, get by date, get by stock, get recent, reject, feedback."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))

    # Save
    d1 = {
        "decision_id": "dec-001",
        "date": "2026-07-06",
        "stock_code": "002415",
        "stock_name": "Hikvision",
        "rank": 1,
        "score": 8.5,
        "confidence": 0.75,
        "deep_dive": True,
        "suggested_action": "review",
    }
    repo.save_decision(d1)

    d2 = {
        "decision_id": "dec-002",
        "date": "2026-07-06",
        "stock_code": "600519",
        "stock_name": "Moutai",
        "rank": 2,
        "score": 7.0,
        "confidence": 0.60,
        "deep_dive": False,
        "suggested_action": "watch",
    }
    repo.save_decision(d2)

    # Get by date
    by_date = repo.get_decisions_by_date("2026-07-06")
    assert len(by_date) == 2

    # Get by stock
    by_stock = repo.get_decisions_by_stock("002415")
    assert len(by_stock) == 1
    assert by_stock[0]["stock_name"] == "Hikvision"

    # Get recent decisions
    recent = repo.get_recent_decisions(5)
    assert len(recent) == 2

    # Rejected stocks (none yet)
    assert repo.get_rejected_stocks(20) == []

    # Update feedback
    repo.update_decision_feedback("dec-001", "confirmed")
    decisions = repo.get_decisions_by_date("2026-07-06")
    assert decisions[0]["user_feedback"] == "confirmed"

    repo.close()


def test_rejected_stocks_filtering(tmp_path):
    """Rejected stocks should be returned filtered by feedback."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))

    repo.save_decision({
        "decision_id": "dec-r1",
        "date": "2026-07-06",
        "stock_code": "002415",
        "stock_name": "Hikvision",
    })
    repo.update_decision_feedback("dec-r1", "rejected")

    repo.save_decision({
        "decision_id": "dec-r2",
        "date": "2026-07-06",
        "stock_code": "600519",
        "stock_name": "Moutai",
    })
    repo.update_decision_feedback("dec-r2", "confirmed")

    rejected = repo.get_rejected_stocks(20)
    assert rejected == ["002415"]

    repo.close()


def test_auto_initialize(tmp_path):
    """Calling a read method without initialize() should auto-initialize."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))
    # Skip explicit initialize()
    wl = repo.get_watchlist()
    assert wl == []  # Empty, but no error
    repo.close()


def test_lazy_connection(tmp_path):
    """__init__ should not create the database file or open a connection."""
    from memory.repository import MemoryRepository
    import os

    db_path = str(tmp_path / "test.db")
    repo = MemoryRepository(db_path)
    assert not os.path.exists(db_path)  # No file created yet
    assert repo._conn is None           # No connection opened
    repo.close()
def test_repository_initialization_creates_tables(tmp_path):
    """initialize() should create the database file and all three tables."""
    from memory.repository import MemoryRepository

    db_path = str(tmp_path / "test.db")
    repo = MemoryRepository(db_path)
    repo.initialize()

    # Database file exists
    assert os.path.exists(db_path)

    # All three tables exist
    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t[0] for t in tables]

    assert "watchlist" in table_names
    assert "market_snapshots" in table_names
    assert "decisions" in table_names

    # Schema version table exists with correct version
    version = conn.execute("SELECT version FROM schema_version").fetchone()
    assert version[0] == 2

    conn.close()
    repo.close()


def test_source_status_save_and_get(tmp_path):
    """save_source_status should write and get_source_status should read back."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))

    repo.save_source_status("tushare", "success", None)
    repo.save_source_status("akshare", "partial", "macro fetch timeout")

    today = repo._now_date(); records = repo.get_source_status(today)
    assert len(records) == 2
    assert records[0]["source"] == "tushare"
    # verify all records have today's date
    today = repo._now_date()
    for r in records:
        assert r["date"] == today
    assert records[0]["status"] == "success"
    assert records[0]["error_message"] is None
    assert records[1]["source"] == "akshare"
    assert records[1]["status"] == "partial"
    assert records[1]["error_message"] == "macro fetch timeout"

    repo.close()


def test_source_status_filter_by_date(tmp_path):
    """get_source_status should only return records for the given date."""
    from memory.repository import MemoryRepository

    repo = MemoryRepository(str(tmp_path / "test.db"))
    repo.save_source_status("tushare", "success")

    # Query a different date — should be empty
    # Query a different date — should be empty
    records = repo.get_source_status("2026-01-01")
    assert records == []

    repo.close()


def test_source_status_initialization_creates_table(tmp_path):
    """data_source_status table should be created on initialization."""
    import sqlite3
    from memory.repository import MemoryRepository

    db_path = str(tmp_path / "test.db")
    repo = MemoryRepository(db_path)
    repo.initialize()

    conn = sqlite3.connect(db_path)
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t[0] for t in tables]

    assert "data_source_status" in table_names

    conn.close()
    repo.close()



