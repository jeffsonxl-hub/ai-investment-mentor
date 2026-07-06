# ADR-005: Dual-Source Data Strategy (TuShare + AkShare)

## Status
Accepted

## Context

The AI Investment Mentor decision flow defines five data categories required for a complete daily analysis:

1. **Market data** — index OHLCV, sector-level returns, daily stock prices/volume
2. **Fundamental data** — PE, PB, ROE, revenue growth rate, market cap, industry classification
3. **Macro data** — SHIBOR overnight rate, PBOC policy signals, PMI, CPI
4. **Capital flow** — north-bound net flow through Stock Connect (沪深港通)
5. **News & announcements** — company filings, policy news, earnings guidance, material events

The Chinese A-share ecosystem has two major open/free Python libraries, but their coverage profiles differ significantly. Neither alone covers all five categories at acceptable reliability. A decision must be made on which library serves which data category, and how the data layer should be architected around that division.

Key constraints:
- V1 is a single-user personal tool running a daily morning pipeline
- The project is built in Python with an `asyncio`-based DAG Pipeline (ADR-004)
- The system must degrade gracefully — missing data is better than a crashed pipeline
- The Pipeline targets < 120 seconds end-to-end for the daily run
- Agents (Phases 8–11) will depend on the data layer being in place first

## Decision

We adopt a **dual-source strategy** with a single `DataProvider` Component as the unified interface:

| Data Category | Primary Source | Fallback | Rationale |
|---|---|---|---|
| Market data (OHLCV, prices) | TuShare | AkShare | TuShare's `daily()` is stable, battle-tested, and returns clean adjusted data with trading status flags |
| Fundamental data | TuShare | None | TuShare's financial statement coverage is its strongest feature. AkShare's fundamentals are scraping-dependent and unreliable |
| Macro data (SHIBOR, PMI, CPI) | AkShare | None | AkShare wraps government data portals that rarely change. TuShare's macro coverage is thin |
| Capital flow (northbound) | AkShare | None | AkShare scrapes East Money's intraday flow data. TuShare's flow endpoints are more limited |
| News & announcements | AkShare | None | AkShare's `stock_news_em()` and exchange scraping cover this. TuShare has no equivalent |
| Sector/industry mapping | AkShare | None | Tonghuashun-based sector classification via AkShare is more granular than TuShare's |

**Architecture**: A single `DataProvider` Component wraps two internal clients (`AkShareClient`, `TuShareClient`). Agents call `DataProvider.get_fundamentals(codes)` — they never know which library is underneath. Rate limiting, fallback logic, and error handling are internal to the Component.

**Rate limiting**: TuShare calls are sequential (semaphore of 1) to respect the free-tier concurrency limit. AkShare calls are parallel (semaphore of 10) since they hit different upstream websites. The daily call budget (~80–100 total API calls) fits comfortably within TuShare's free-tier limit of 200–500 calls/day.

**No caching in V1**: A once-daily pipeline fetches fresh data by definition. Caching adds state management and invalidation logic with no benefit for this access pattern. Revisit in V2 for intraday re-runs and backtesting.

**Graceful degradation**: If TuShare is unavailable, flag missing fundamental data and continue with market/macro/news from AkShare. If AkShare is unavailable, lose news/northbound but preserve the core market regime analysis. The pipeline never crashes because a data source is down.

## Consequences

**What becomes easier:**
- **Full data coverage.** All five categories are served by their best available source
- **Single interface for Agents.** Agents call one Component with typed methods — no data-source awareness leaked into the Agent layer
- **Enforced rate discipline.** TuShare sequential queuing and per-fetch timeouts are centralized, not scattered across agents
- **Observability.** A `data_source_status` table in SQLite logs which sources succeeded or failed each day, making debugging straightforward

**What becomes harder:**
- **Two dependency upgrade paths.** Both `akshare` and `tushare` versions must be tracked. AkShare in particular has frequent breaking releases — we pin versions in `requirements.txt` with exact constraints
- **AkShare fragility.** AkShare scrapes unofficial endpoints. When East Money or Sina Finance changes an internal API, AkShare breaks until the community patches it. Our `DataProvider` must handle `ImportError` and HTTP errors gracefully
- **TuShare sequential bottleneck.** With a semaphore of 1, TuShare calls cannot be parallelized. For a 50-stock fundamental fetch, we batch codes into a single API call where possible to amortize the sequential cost

## Alternatives Considered

### Alternative A: TuShare-only
Use TuShare for everything. Rejected because TuShare has weak macro coverage and no news/announcement endpoints. Two of five data categories would be missing.

### Alternative B: AkShare-only
Use AkShare for everything. Rejected because AkShare's fundamental data is scraping-dependent and unreliable. The scoring engine's most important dimension (fundamental quality) would be built on shaky data.

### Alternative C: One Component per data category
Separate `MarketDataProvider`, `FundamentalProvider`, `MacroProvider`, `NewsProvider`. Rejected for V1 because: (a) with only 4 agents total, fragmenting the interface creates more files without a clear consumer benefit, (b) centralized rate limiting is harder with five independent components, (c) can be split later if Phase 8–11 proves agents need independent data access patterns.
