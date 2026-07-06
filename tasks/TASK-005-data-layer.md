# TASK-005: Data Layer Implementation

## Context

Phase 5 — Data Layer Design. ADR-005 establishes a dual-source strategy: TuShare for stable structured data (OHLCV, fundamentals), AkShare for breadth coverage (macro, northbound flow, news). The design document at `docs/architecture/06-data-layer-design.md` defines three Components: `AkShareClient`, `TuShareClient`, and `DataProvider`.

Read these first:
- `adr/ADR-005-data-source-strategy.md` — why dual-source
- `docs/architecture/06-data-layer-design.md` — full architecture with interface contracts
- `adr/ADR-003-memory-strategy.md` — existing memory layer context
- `components/memory-repository.md` — MemoryRepository interface (DataProvider depends on it)

## Objective

Implement the data layer: two client wrappers (AkShare, TuShare) and a unified DataProvider Component that Agents will call. Extend MemoryRepository with data source status tracking.

## Requirements

### 1. New Source Files

- [ ] `src/data/__init__.py` — re-exports DataProvider, AkShareClient, TuShareClient, DataFetchError
- [ ] `src/data/exceptions.py` — `DataFetchError` exception class (wraps source name + original exception)
- [ ] `src/data/ak_share_client.py` — `AkShareClient` wrapping akshare library
- [ ] `src/data/tu_share_client.py` — `TuShareClient` wrapping tushare library with sequential rate limiting
- [ ] `src/data/provider.py` — `DataProvider` orchestrating both clients with graceful degradation

### 2. AkShareClient

- [ ] Constructor: no arguments, sets `_semaphore = asyncio.Semaphore(10)`
- [ ] `async get_index_daily(symbol: str) -> list[dict]` — wraps `akshare.stock_zh_index_daily()`, runs in `run_in_executor`
- [ ] `async get_sector_performance() -> list[dict]` — wraps `akshare.stock_board_industry_summary_ths()`
- [ ] `async get_shibor() -> dict` — wraps `akshare.macro_china_shibor_all()`, returns `{overnight, 1w, ...}`
- [ ] `async get_pmi() -> float | None` — wraps `akshare.macro_china_pmi()`, extracts latest value
- [ ] `async get_cpi() -> float | None` — wraps `akshare.macro_china_cpi_yearly()`, extracts latest value
- [ ] `async get_northbound_flow() -> dict` — wraps `akshare.stock_hsgt_north_net_flow_in_em()`, returns `{sh_net, sz_net, total_net}`
- [ ] `async get_stock_news(stock_code: str, limit: int = 20) -> list[dict]` — wraps `akshare.stock_news_em()`, normalizes to `{title, content, publish_time, source}`
- [ ] `async get_announcements(stock_code: str, limit: int = 20) -> list[dict]` — wraps `akshare.stock_info_sh_name_code()`, normalizes to `{title, type, publish_date, summary}`
- [ ] All methods: wrapped in try/except, return empty `[]` or `None` on failure, log warning, never raise

### 3. TuShareClient

- [ ] Constructor: takes `token: str`, creates `tushare.pro_api(token)`, sets `_semaphore = asyncio.Semaphore(1)`
- [ ] `async get_daily(trade_date: str) -> list[dict]` — wraps `pro.daily(trade_date=date)`, returns normalized `{ts_code, open, high, low, close, vol, amount}`
- [ ] `async get_stock_basic() -> list[dict]` — wraps `pro.stock_basic(list_status='L')`, returns `{ts_code, name, industry, market, list_date}`
- [ ] `async get_daily_basic(trade_date: str, ts_codes: list[str] | None = None) -> list[dict]` — wraps `pro.daily_basic()`, returns `{ts_code, pe, pb, total_mv, turnover_rate}`
- [ ] `async get_income(ts_codes: list[str], period: str) -> list[dict]` — wraps `pro.income()`, batches codes as comma-separated string
- [ ] `async get_index_daily(ts_code: str, start_date: str, end_date: str) -> list[dict]` — wraps `pro.index_daily()`
- [ ] All methods: acquire semaphore, call TuShare, return normalized dicts
- [ ] All methods: wrap in try/except, raise `DataFetchError` on failure
- [ ] Timeout: 15 seconds per call (use `asyncio.wait_for`)

### 4. DataProvider

- [ ] Constructor: takes `TuShareClient`, `AkShareClient`, `MemoryRepository` via dependency injection
- [ ] `async get_market_snapshot(date: str) -> dict` — orchestrates index data (TuShare), macro (AkShare), northbound flow (AkShare) in parallel; returns unified dict with `data_quality` flag
- [ ] `async get_index_data(start_date: str, end_date: str) -> list[dict]` — TuShare primary, AkShare fallback
- [ ] `async get_sector_performance() -> list[dict]` — delegates to AkShare
- [ ] `async get_fundamental_snapshot(ts_codes: list[str], date: str) -> list[dict]` — delegates to TuShare for daily_basic + income
- [ ] `async get_stock_basic_info() -> list[dict]` — delegates to TuShare
- [ ] `async get_macro_indicators() -> dict` — delegates to AkShare for SHIBOR + PMI + CPI
- [ ] `async get_northbound_flow() -> dict` — delegates to AkShare
- [ ] `async get_stock_news(stock_code: str, limit: int = 20) -> list[dict]` — delegates to AkShare
- [ ] `async get_announcements(stock_code: str, limit: int = 20) -> list[dict]` — delegates to AkShare
- [ ] `async _record_source_status(source: str, status: str, error: str | None) -> None` — writes to MemoryRepository
- [ ] `async get_source_status(date: str) -> list[dict]` — reads from MemoryRepository
- [ ] Every method records source status after execution

### 5. Database Schema Extension

- [ ] Add `CREATE_DATA_SOURCE_STATUS` table definition to `src/memory/schema.py`
- [ ] Add `CREATE_DATA_SOURCE_STATUS_INDEXES` (index on date, source)
- [ ] Add both to `ALL_TABLES` and `ALL_INDEXES` lists
- [ ] Bump `SCHEMA_VERSION` to 2

### 6. MemoryRepository Extension

- [ ] Add `save_source_status(source: str, status: str, error_message: str | None) -> None` to `src/memory/repository.py`
- [ ] Add `get_source_status(date: str) -> list[dict]` to `src/memory/repository.py`
- [ ] Both methods follow existing MemoryRepository patterns (typed, no raw SQL exposed, wrapped errors)

### 7. Configuration Extension

- [ ] Add `[data]` section to `src/config.py` with: `tushare_token`, `tushare_call_timeout`, `akshare_call_timeout`, `akshare_parallel_limit`, `news_default_limit`
- [ ] `tushare_token` reads from env var `TUSHARE_TOKEN`
- [ ] Sensible defaults for all timeout/limit values

### 8. Dependencies

- [ ] Add `akshare>=1.14.0` to `requirements.txt` (pin major.minor due to frequent breaking changes)
- [ ] Add `tushare>=1.4.0` to `requirements.txt`

### 9. Tests

- [ ] `tests/test_ak_share_client.py` — mock `akshare` module, test each method returns dicts, test failure returns `[]`, test semaphore limit is respected
- [ ] `tests/test_tu_share_client.py` — mock `tushare.pro_api`, test each method returns dicts, test sequential enforcement, test timeout, test raises `DataFetchError`
- [ ] `tests/test_provider.py` — mock both clients + MemoryRepository, test `get_market_snapshot()` orchestrates correctly, test graceful degradation when one client fails, test source status recording
- [ ] `tests/test_memory_repository.py` — extend existing tests for `save_source_status()` and `get_source_status()` (this is the same file from Phase 3, add test methods)
- [ ] All tests pass with `pytest`

## Acceptance Criteria

1. `pytest` passes with zero failures
2. `DataProvider.get_market_snapshot()` returns a dict with keys: `date, indices, macro, northbound_flow, data_quality`
3. When TuShare is mocked to fail, `data_quality == 'degraded'` and indices fall back to AkShare
4. When both clients are mocked to fail, `data_quality == 'failed'` and the method does not raise
5. `_record_source_status()` is called after every DataProvider method execution
6. `MemoryRepository.save_source_status()` writes to SQLite and `get_source_status()` reads it back
7. `TuShareClient` enforces sequential calls (test: two concurrent calls, second waits for first)
8. `AkShareClient` enforces max 10 concurrent calls

## Out of Scope

- No Agent integration (Phases 8–11)
- No Pipeline integration — DataProvider is built and tested standalone
- No caching layer (V2)
- No real API calls in tests — everything is mocked
- No LangGraph state integration (Phase 12+)
- No data validation beyond type normalization (e.g., checking that PE values are within reasonable ranges)

## References

- [ADR-005: Data Source Strategy](../adr/ADR-005-data-source-strategy.md)
- [Data Layer Design](../docs/architecture/06-data-layer-design.md)
- [ADR-003: Memory Strategy](../adr/ADR-003-memory-strategy.md)
- [MemoryRepository Spec](../components/memory-repository.md)
