# TASK-003: Memory Layer Implementation

## Context
This task implements the MemoryRepository Component and the SQLite database schema defined in the memory design. It is the second Codex implementation task, following TASK-001 (Project Bootstrap).

**Required reading (in order):**
1. `docs/architecture/05-memory-design.md` ！ full memory architecture, all three schemas
2. `components/memory-repository.md` ！ Component spec with full public interface
3. `adr/ADR-003-memory-strategy.md` ！ why hybrid + SQLite
4. `adr/ADR-002-agent-responsibilities.md` ！ data access boundaries

## Objective
Implement the `MemoryRepository` class exactly as specified in `components/memory-repository.md`. Create the SQLite schema for all three memory types. Write unit tests that verify every public method. **No business logic, no Agent code, no LLM calls.**

## Requirements

### Database Setup
- [ ] Create `src/memory/` package with `__init__.py`
- [ ] Implement `src/memory/repository.py` with the `MemoryRepository` class
- [ ] Implement `src/memory/schema.py` with `CREATE TABLE` and `CREATE INDEX` statements as constants
- [ ] Database path is configurable via config (default: `data/ai_mentor.db`)
- [ ] On `initialize()`, create all tables and indexes with `IF NOT EXISTS`
- [ ] Enable SQLite WAL journal mode on initialize
- [ ] Create version table: `CREATE TABLE IF NOT EXISTS schema_version (version INTEGER)`
- [ ] On initialize, check version matches expected version (V1 = 1)

### MemoryRepository Class
Implement every method listed in the Component Spec Public Interface:

- [ ] Lifecycle: `__init__(db_path)`, `initialize()`, `close()`
- [ ] Watchlist: `get_watchlist()`, `get_watchlist_entry()`, `add_to_watchlist()`, `remove_from_watchlist()`, `update_watchlist_priority()`, `touch_watchlist_entry()`
- [ ] Market: `get_latest_market_snapshot()`, `get_market_snapshot()`, `get_market_snapshot_range()`, `save_market_snapshot()`, `get_regime_history()`
- [ ] Decision: `save_decision()`, `get_decisions_by_date()`, `get_decisions_by_stock()`, `get_recent_decisions()`, `get_rejected_stocks()`, `update_decision_feedback()`

### Error Handling
- [ ] Define `MemoryRepositoryError` exception in `src/memory/exceptions.py`
- [ ] All SQLite errors are caught and re-raised as `MemoryRepositoryError`
- [ ] Auto-initialize: if a method is called before `initialize()`, call it automatically (idempotent)
- [ ] `add_to_watchlist()` raises `ValueError` on duplicate stock code
- [ ] `update_watchlist_priority()` raises `ValueError` if stock not found
- [ ] `remove_from_watchlist()` is idempotent (no error if already removed)

### Tests
- [ ] Create `tests/test_memory_repository.py`
- [ ] Use `tmp_path` fixture for an isolated SQLite database per test
- [ ] Test every public method with at least one happy-path case
- [ ] Test `add_to_watchlist` with duplicate (expects `ValueError`)
- [ ] Test `update_watchlist_priority` with nonexistent stock (expects `ValueError`)
- [ ] Test `remove_from_watchlist` twice (idempotent)
- [ ] Test `get_latest_market_snapshot` on empty table (returns `None`)
- [ ] Test `save_market_snapshot` + `get_market_snapshot` round-trip
- [ ] Test `get_recent_decisions` with varying day ranges
- [ ] Test `get_rejected_stocks` filtering
- [ ] Test auto-initialize: call a read method without calling `initialize()` first ！ it should work

## Acceptance Criteria

1. `pytest tests/test_memory_repository.py` ！ all tests pass
2. `memory_repository.initialize()` creates the database file at the configured path
3. All three table schemas match `docs/architecture/05-memory-design.md` exactly
4. No method accepts or returns raw SQL ！ all data is dicts and lists
5. `MemoryRepository.__init__()` does not open a database connection (lazy connection)
6. `MemoryRepository` has no imports from `openai`, `langgraph`, or any LLM-related package

## Out of Scope

- Async methods (`aiosqlite`) ！ sync-only for V1
- Migration framework (Alembic or custom)
- Read replicas or multi-database support
- Any Agent code that calls MemoryRepository
- Database backup/restore utilities
- Data seeding or migration from JSON files

## References
- `docs/architecture/05-memory-design.md` ！ Schema definitions and access patterns
- `components/memory-repository.md` ！ Full public interface specification
- `adr/ADR-003-memory-strategy.md` ！ Why hybrid + SQLite
- `PROJECT_RULES.md` ！ Section 4 (Component Template) and Section 6 (TASK Standard)


