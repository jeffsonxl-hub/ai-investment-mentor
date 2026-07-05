# Agent Design ¡ª AI Investment Mentor

This document defines every Agent in the AI Investment Mentor system using the standard Agent Specification Template defined in PROJECT_RULES.md. Each Agent design answers: who it is, what it does, what it needs, and what it produces.

## Design Principle: Specialist Agents, One Advisor

The system splits intelligence across four specialist Agents plus one Advisor Agent that synthesizes their output:

```
Market Agent ©¤©¤©´
Research Agent ©¤©È
Watchlist Agent ©¤©à©¤©¤? Advisor Agent ©¤©¤? User (Morning Report)
``` 

No Agent talks to another Agent directly. Every Agent produces structured output consumed by the Advisor. This keeps each Agent independently testable, swappable, and debuggable.

---

# Market Agent

## Identity
A macro-market analyst that reads the broad A-share environment. It does not pick individual stocks ¡ª it answers "what kind of market are we in right now?"

## Purpose
Assess the current market regime, sector rotation patterns, and macro liquidity conditions so downstream agents can filter stocks appropriate to the environment.

## Goal
Produce a daily Market Context object that classifies the trading day into a regime type (risk-on, risk-off, neutral, rotational) with supporting evidence.

## Inputs
| Input | Source | Description |
|---|---|---|
| Index data | Data Layer (AkShare/TuShare) | Shanghai Composite, Shenzhen Component, ChiNext, STAR 50 ¡ª daily OHLCV |
| Sector performance | Data Layer | Sector-level returns, volume, relative strength |
| North-bound capital flow | Data Layer | Daily net flow and cumulative trend |
| Monetary policy signals | Research Agent (structured output) | SHIBOR, reverse repo, PBOC announcements |
| Previous Market Context | Memory (Market) | Yesterday regime and signals for trend comparison |

## Outputs
```json
{
  "date": "2026-07-04",
  "regime": "risk_on | risk_off | neutral | rotational",
  "confidence": 0.0 - 1.0,
  "evidence": [
    {"signal": "index_breadth", "value": "75% of sectors above 20-day MA"},
    {"signal": "volume_trend", "value": "3-day average volume 15% above 20-day average"}
  ],
  "leading_sectors": ["semiconductors", "precious_metals"],
  "lagging_sectors": ["real_estate", "consumer_electronics"],
  "risk_flags": ["geopolitical_tension_taiwan", "earnings_season_peak"],
  "macro_narrative": "Tech rotation continues with volume confirmation. Caution: earnings season begins next week."
}
```

## Memory
- **Reads** Market Memory for yesterday context (regime trend comparison)
- **Writes** Market Memory with today assessment

## Tools
| Tool | Purpose |
|---|---|
| `get_index_data(date)` | Fetch OHLCV for major indices |
| `get_sector_performance(date)` | Sector-level returns and volume data |
| `get_northbound_flow(date_range)` | North-bound capital flow trend |
| `get_shibor(tenor)` | Interbank lending rates (liquidity proxy) |

## Workflow
1. Load yesterday Market Context from Memory for trend comparison
2. Fetch today index data and compute breadths, volume ratios, moving average positions
3. Fetch sector performance ¡ª identify top 3 and bottom 3 sectors by return
4. Fetch north-bound flow and SHIBOR for liquidity signal
5. Consume structured macro summary from Research Agent (policy events)
6. Classify regime using a deterministic rule engine first (breadth, volume, sector dispersion thresholds)
7. If rule engine confidence is below 0.6, invoke LLM with structured evidence to produce final classification and narrative
8. Write result to Market Memory and return structured output

## Constraints
- Never references individual stocks. This is macro only
- Never makes trade recommendations
- Deterministic rule engine runs first ¡ª LLM is a fallback, not the default

## Consumers
- **Advisor Agent** ¡ª regime classification drives candidate stock filtering
- **Watchlist Agent** ¡ª regime context provides baseline for watchlist alert generation (V2)

## Failure Handling
- If data sources are unavailable, return a "data degraded" flag in output with partial results
- If LLM call fails after rule engine, return rule engine output with a "LLM fallback skipped" flag
- Never block downstream agents ¡ª always produce a best-effort Market Context

## Future Evolution
- Add historical regime labeling for backtesting
- Add sentiment signal from social media / news volume
- Multi-timeframe analysis (weekly overlay on daily)

---

# Research Agent

## Identity
An intelligence analyst that converts unstructured information (news, announcements, policy, social sentiment) into structured facts. It does not make investment judgments ¡ª it extracts and classifies information.

## Purpose
Read, categorize, and summarize external information so the Advisor Agent receives clean, structured evidence instead of raw news feeds.

## Goal
For a given universe of stocks (or a market-wide scan), produce a set of structured Event records with source attribution, relevance scoring, and sentiment classification.

## Inputs
| Input | Source | Description |
|---|---|---|
| Stock universe | Advisor Agent (via TASK) | List of stock codes to research, or "market-wide" flag |
| News feeds | Data Layer | Financial news APIs, official media, industry publications |
| Company announcements | Data Layer | SSE/SZSE disclosure system |
| Policy documents | Data Layer | PBOC, CSRC, NDRC announcements |
| Social sentiment (V2) | Data Layer | Aggregated sentiment from Xueqiu, Eastmoney forums |

## Outputs
```json
{
  "events": [
    {
      "event_id": "evt-20260704-001",
      "stock_code": "600519",
      "event_type": "earnings_guidance | policy_impact | product_news | management_change | industry_trend | other",
      "sentiment": "positive | negative | neutral",
      "relevance_score": 0.0 - 1.0,
      "summary": "Kweichow Moutai raises ex-factory price by 15% effective August 2026. Direct impact on Q3 revenue.",
      "source": "SSE announcement 2026-07-04",
      "source_url": "http://...",
      "timestamp": "2026-07-04T08:00:00Z",
      "keywords": ["price_increase", "liquor", "consumer_staples", "earnings_catalyst"]
    }
  ],
  "market_wide_summary": {
    "top_themes": ["AI_rotation", "precious_metals_strength"],
    "policy_events": ["PBOC maintains LPR, signals possible cut in Q3"],
    "risk_events": ["Taiwan semiconductor export controls update expected this week"]
  }
}
```

## Memory
- **Reads** Decision Memory for past event relevance calibration (which event types historically drove price moves)
- **Writes** Decision Memory with new events for future trend analysis (V2)

## Tools
| Tool | Purpose |
|---|---|
| `fetch_news(stock_code, date_range)` | Retrieve news articles for a stock or market-wide |
| `fetch_announcements(stock_code, date)` | Retrieve SSE/SZSE announcements |
| `summarize_article(url)` | Extract and summarize a single article using LLM |
| `classify_event(text)` | Classify unstructured text into event_type + sentiment |

## Workflow
1. Receive target stock universe or "market-wide" scope from Advisor
2. Fetch news and announcements for each stock (parallel where possible)
3. For each article, run extraction + classification pipeline
4. Deduplicate events (same story from multiple sources)
5. Score relevance: how likely is this to matter for a short-to-medium-term investor?
6. Generate market-wide summary: aggregate themes, policy signals, risk events
7. Write events to Decision Memory (for future pattern learning, V2)
8. Return structured Event list and market-wide summary

## Constraints
- Never rates a stock as "buy" or "sell" ¡ª this Agent classifies information, it does not recommend
- Every event must include a source URL for auditability
- Sentiment classification must be verifiable against the source text ¡ª no hallucinated sentiment

## Consumers
- **Advisor Agent** ¡ª events are the primary evidence for candidate scoring
- **Market Agent** ¡ª market-wide summary contributes to regime assessment (policy events)

## Failure Handling
- If news API is unavailable, flag output as "data degraded" and return only announcements
- If a specific stock has no news, return empty event list (not an error)
- If LLM summarization fails for one article, skip it and log ¡ª do not fail the entire batch
- If all sources are unavailable, return empty output with degradation flag

## Future Evolution
- Entity extraction: link events to specific products, competitors, supply chain nodes
- Event correlation: detect when multiple stocks are affected by the same catalyst
- Historical event-to-price-move mapping for relevance calibration

---

# Watchlist Agent

## Identity
A personal portfolio tracker that maintains the user curated watchlist and tracks changes over time. It recommends additions and removals but never acts without user approval.

## Purpose
Maintain the user personalized watchlist so the Advisor can prioritize stocks the user actually cares about, and alert the user to meaningful changes in watched stocks.

## Goal
Manage the watchlist lifecycle (add, remove, alert) and produce a daily Watchlist Status report showing what changed overnight for each watched stock.

## Inputs
| Input | Source | Description |
|---|---|---|
| Current watchlist | Memory (Watchlist) | List of stock codes the user is tracking |
| User commands | User (via Advisor) | Add/remove requests, priority changes |
| Market data | Data Layer | Price, volume, technical signals for watched stocks |
| Events | Research Agent | News and announcements specifically for watched stocks |

## Outputs
```json
{
  "watchlist": [
    {
      "stock_code": "600519",
      "added_date": "2026-06-15",
      "added_reason": "User request",
      "priority": "high | medium | low",
      "last_reviewed": "2026-07-03",
      "alerts": [
        {"type": "price_alert", "message": "Down 5% from weekly high", "severity": "medium"}
      ]
    }
  ],
  "recommendations": [
    {
      "action": "add",
      "stock_code": "002415",
      "reason": "Appears in top-scoring candidates for 5 consecutive days",
      "confidence": 0.8
    }
  ],
  "daily_summary": "3 of 12 watched stocks had significant news today. 600519 price alert triggered."
}
```

## Memory
- **Reads/Writes** Watchlist Memory ¡ª the canonical watchlist store
- **Reads** Market Memory ¡ª for regime context when generating alerts

## Tools
| Tool | Purpose |
|---|---|
| `get_watchlist()` | Read full watchlist from Memory |
| `add_to_watchlist(stock_code, reason)` | Add stock (triggers user confirmation in Advisor) |
| `remove_from_watchlist(stock_code, reason)` | Remove stock (triggers user confirmation) |
| `check_alerts(stock_code)` | Generate alerts for a watched stock based on price/volume/news |

## Workflow
1. Load current watchlist from Memory
2. For each watched stock, fetch latest price and compare against recent history
3. Cross-reference with Research Agent events for watched stocks specifically
4. Generate alerts: price thresholds breached, significant news, volume anomalies
5. Scan Advisor candidate history ¡ª if a stock repeatedly appears in top picks but is not watched, recommend adding it
6. Scan watchlist for stale entries: stocks not reviewed in 30+ days, recommend removal
7. Return Watchlist Status with alerts and recommendations
8. (User approves/rejects recommendations via Advisor ¡ª Watchlist Agent never modifies the list directly)

## Constraints
- Never adds or removes stocks without explicit user confirmation
- Recommendations must include a reason ¡ª never "this stock is hot"
- Alerts must be actionable ¡ª "down 5%" is an observation, "down 5% on high volume after earnings miss" is an alert

## Consumers
- **Advisor Agent** ¡ª watchlist priorities influence candidate scoring weight
- **User** ¡ª alerts and recommendations are presented in the morning report

## Failure Handling
- If watchlist is empty (first-time user), return empty status with a guidance message for the Advisor to present
- If market data for a watched stock is unavailable (suspended, delisted), flag it and recommend review
- Never lose the watchlist ¡ª all write operations are atomic

## Future Evolution
- Performance tracking: tag watchlist entries with "since added" performance
- Smart categories: user can tag stocks as "long-term hold," "swing trade," "just watching"
- Correlation alerts: flag when multiple watchlist stocks share exposure to the same risk factor

---

# Advisor Agent

## Identity
The user-facing investment mentor. It does not gather raw data ¡ª it synthesizes structured output from all specialist Agents into a readable, evidence-backed morning report. It is the only Agent the user directly interacts with.

## Purpose
Generate a daily morning report that explains which stocks deserve attention and why, teaching the user to think like an investor in the process.

## Goal
From the full A-share market (~5000 stocks), produce a morning report with 5¨C10 explainable candidates and one deep-dive pick ¡ª all with evidence chains the user can verify and learn from.

## Inputs
| Input | Source | Description |
|---|---|---|
| Market Context | Market Agent | Regime classification, sector momentum, risk flags |
| Events | Research Agent | Structured news, announcements, policy impacts |
| Watchlist Status | Watchlist Agent | User watched stocks with alerts and recommendations |
| Decision History | Memory (Decision) | Past recommendations, user feedback, outcomes |
| User Preferences | Memory (Watchlist) | Priority sectors, risk tolerance (V2) |

## Outputs
A Morning Report structured as:

```json
{
  "report_date": "2026-07-04",
  "market_summary": {
    "regime": "risk_on",
    "narrative": "Tech rotation continues with strong volume. Precious metals bid on policy uncertainty.",
    "risk_warning": "Earnings season starts next week ¡ª guidance risk elevated for high-multiple names."
  },
  "candidates": [
    {
      "rank": 1,
      "stock_code": "002415",
      "stock_name": "Hikvision",
      "score": 8.5,
      "score_breakdown": {
        "fundamental": 7.0,
        "technical": 8.5,
        "news_sentiment": 9.0,
        "capital_flow": 8.0
      },
      "thesis": "AI surveillance demand cycle turning up. Institution buying accelerating. Q2 guidance above consensus.",
      "evidence": [
        {"source": "Research Agent", "type": "earnings_guidance", "summary": "Hikvision pre-announced Q2 revenue +22% YoY"},
        {"source": "Market Agent", "type": "sector_momentum", "summary": "AI sector ranked #1 this week, breadth expanding"},
        {"source": "Data Layer", "type": "capital_flow", "summary": "North-bound net buy 3 consecutive days"}
      ],
      "risks": ["US sanctions escalation", "Government budget constraints on surveillance spending"],
      "confidence": 0.75,
      "suggested_action": "review",
      "watchlist_status": "already_watched"
    }
  ],
  "deep_dive": {
    "stock_code": "002415",
    "stock_name": "Hikvision",
    "business_summary": "China largest video surveillance company. AIoT pivot driving new growth verticals.",
    "catalyst": "Q2 earnings beat + new government smart city contracts expected in Q3",
    "valuation_context": "Trades at 22x forward earnings vs 5-year average of 28x. Below historical median despite improving fundamentals.",
    "risk_scenario": "If US expands Entity List restrictions, overseas revenue (~30%) at risk. Estimated downside: 15-20%.",
    "price_zone": "Current range 32-35. Strong support at 30 (200-day MA). Watching for breakout above 36 on volume.",
    "invalidation": "If Q2 actual results show margin contraction or overseas revenue decline, thesis is broken."
  },
  "watchlist_alerts": [...],
  "learning_point": "Today deep dive illustrates a classic setup: improving fundamentals (earnings acceleration) combined with depressed valuation (below historical median). The market has not yet fully priced the earnings inflection. Key to watch: does volume confirm the move, or is this a false breakout?"
}
```

## Memory
- **Reads** Decision Memory ¡ª past recommendations, user feedback, outcome data (V2)
- **Reads** Watchlist Memory ¡ª user preferences and watched stocks
- **Reads** Market Memory ¡ª historical regime context
- **Writes** Decision Memory ¡ª today recommendations with full evidence chains

## Tools
The Advisor Agent does not call data-source tools directly. It only calls orchestration and presentation tools:

| Tool | Purpose |
|---|---|
| `request_market_context()` | Trigger Market Agent and receive structured Market Context |
| `request_events(stock_codes)` | Trigger Research Agent for specific stocks |
| `request_watchlist_status()` | Trigger Watchlist Agent for daily status |
| `score_candidates(candidates, context)` | Deterministic scoring engine that ranks candidates |
| `generate_report(scored_candidates, context)` | LLM-powered narrative generation from structured data |
| `present_to_user(report)` | Format and deliver the morning report |

## Workflow
1. **Gather evidence**: Call Market Agent, Research Agent (market-wide), and Watchlist Agent in parallel
2. **Build candidate universe**: Start from watchlist, expand to stocks matching current regime and themes
3. **Request stock-level research**: Call Research Agent for stock-specific events on candidates
4. **Score candidates**: Run deterministic multi-factor scoring (fundamental, technical, news, capital flow weights adjusted by regime)
5. **Select deep dive**: Highest-scoring candidate with the richest evidence chain
6. **Generate narrative**: LLM synthesizes scored candidates into readable report with learning point
7. **Present report**: Format and deliver to user
8. **Record decision**: Write full report to Decision Memory for future learning

## Constraints
- Never accesses data sources directly ¡ª all data comes through specialist Agents
- Every recommendation must cite at least two independent evidence sources
- Scoring weights must be documented and auditable ¡ª no "vibe-based" rankings
- The learning point is mandatory ¡ª every report must teach one concept
- Never executes trades or sends orders

## Consumers
- **User** ¡ª the sole consumer. The Advisor is the only outward-facing Agent

## Failure Handling
- If one specialist Agent fails, generate report with degraded flag and partial data ¡ª never block the entire report
- If all specialist Agents fail, produce a "service unavailable" message with retry guidance
- If LLM narrative generation fails, fall back to structured bullet-point report without narrative
- User-facing error messages must be calm, specific, and actionable ¡ª never raw stack traces

## Future Evolution
- Personalized scoring: weights adapt to user feedback over time
- Multi-day narrative: track a thesis across multiple reports ("last Thursday we flagged Hikvision at 32 ¡ª today catalysts confirmed at 35")
- Interactive mode: user can ask follow-up questions about a specific candidate and get deeper analysis
