# System Overview ！ AI Investment Mentor

This document describes the high-level architecture of the AI Investment Mentor system: what layers exist, how they communicate, and how a user request flows through the system.

## Architecture Layers

The system is organized into five layers. Each layer depends only on the layer directly below it:

```mermaid
graph TB
    subgraph "User Interface"
        UI["Morning Report<br/>(formatted output)"]
    end

    subgraph "Agent Layer"
        AD["Advisor Agent<br/>Synthesis & Explanation"]
        MA["Market Agent<br/>Regime Assessment"]
        RA["Research Agent<br/>Event Extraction"]
        WA["Watchlist Agent<br/>Portfolio Tracking"]
    end

    subgraph "Tool Layer"
        T1["Market Data Tools<br/>OHLCV, sectors, flows"]
        T2["News Tools<br/>Articles, announcements"]
        T3["Watchlist Tools<br/>CRUD operations"]
        T4["Scoring Engine<br/>Multi-factor ranking"]
    end

    subgraph "Component Layer"
        MR["MemoryRepository<br/>SQLite persistence"]
        CL["ConfigLoader<br/>Environment & settings"]
        LG["Logger<br/>Structured logging"]
    end

    subgraph "Data Layer"
        D1["AkShare / TuShare<br/>Market data"]
        D2["News APIs<br/>Financial news"]
        D3["SSE/SZSE<br/>Announcements"]
        D4["SQLite DB<br/>Local storage"]
    end

    UI --> AD
    AD --> MA
    AD --> RA
    AD --> WA
    MA --> T1
    RA --> T2
    WA --> T3
    AD --> T4
    T1 --> MR
    T2 --> MR
    T3 --> MR
    T4 --> MR
    T1 --> D1
    T2 --> D2
    T2 --> D3
    MR --> D4
    MA --> MR
    RA --> MR
    WA --> MR
    AD --> MR

    style UI fill:#e8f5e9
    style AD fill:#fff3e0
    style MA fill:#fff3e0
    style RA fill:#fff3e0
    style WA fill:#fff3e0
    style T1 fill:#e3f2fd
    style T2 fill:#e3f2fd
    style T3 fill:#e3f2fd
    style T4 fill:#e3f2fd
    style MR fill:#f3e5f5
    style CL fill:#f3e5f5
    style LG fill:#f3e5f5
    style D1 fill:#fce4ec
    style D2 fill:#fce4ec
    style D3 fill:#fce4ec
    style D4 fill:#fce4ec
```

## Layer Descriptions

### User Interface
The user sees a formatted morning report. In V1, this is a text file or terminal output. The UI layer is intentionally minimal ！ the system is an analytical engine, not a web application. Future phases may add a web dashboard (V2).

### Agent Layer
Four specialist Agents plus one Advisor Agent that orchestrates them. Each Agent owns one domain of intelligence. Agents communicate through structured JSON ！ no Agent calls another Agent directly. The Advisor is the only Agent that initiates work.

| Agent | Responsibility | Triggers |
|---|---|---|
| Market Agent | Assess market regime, sector momentum, macro conditions | Daily schedule |
| Research Agent | Extract and classify news, announcements, policy events | On-demand (candidate list) |
| Watchlist Agent | Track user-curated watchlist, generate alerts | Daily schedule |
| Advisor Agent | Orchestrate all agents, score candidates, generate morning report | Daily schedule |

### Tool Layer
Tools are the capabilities Agents can invoke. Each Tool wraps one external operation ！ fetching data, summarizing text, writing to storage. Tools are stateless: they do not remember anything between calls. That job belongs to the Component Layer.

Key design rule: **Agents decide what to do. Tools execute the how.** An Agent never opens a network connection or writes a file directly.

### Component Layer
Infrastructure that persists across Agent invocations. Components are deterministic, have no LLM access, and provide the foundation services every Agent depends on.

| Component | Purpose |
|---|---|
| MemoryRepository | Read/write all three memory types via SQLite |
| ConfigLoader | Load environment variables and configuration files |
| Logger | Structured logging for debugging and audit trails |

### Data Layer
External data sources. The system never assumes a data source is available ！ every call is wrapped with timeout, retry, and degradation logic.

| Source | Provides | Protocol |
|---|---|---|
| AkShare / TuShare | OHLCV, fundamentals, sector data, capital flows | Python library / REST API |
| News APIs | Financial news articles | REST API |
| SSE/SZSE | Company announcements, filings | Web scraping / API |
| SQLite | Local persistence for all memory types | Local file |

## Communication Patterns

### 1. Agent ★ Tool
Synchronous call-return. Agent invokes a tool by name and receives structured data back. Tools do not know which Agent called them.

### 2. Agent ★ Component
Synchronous call-return. Agent reads/writes memory through the MemoryRepository Component. Components present a clean Python interface ！ the Agent never writes SQL.

### 3. Agent ★ Agent
There is no direct Agent-to-Agent communication. The Advisor Agent orchestrates: it calls Market Agent, receives Market Context, then passes relevant parts to Research Agent as parameters. Specialist Agents never call each other.

### 4. Tool ★ Data Layer
Synchronous with timeout (default: 30 seconds) and one automatic retry. If the data source is unavailable, the Tool returns a degradation flag rather than throwing an exception.

## Data Flow: Morning Report Generation

```mermaid
sequenceDiagram
    participant User
    participant Advisor
    participant Market
    participant Research
    participant Watchlist
    participant MR as MemoryRepository

    Note over User,MR: 8:30 AM ！ Daily trigger fires

    Advisor->>Market: request_market_context()
    Market->>MR: read(market_memory, yesterday)
    Market-->>Advisor: Market Context

    Advisor->>Research: request_events(market_wide)
    Research-->>Advisor: Market-wide Events

    Advisor->>Watchlist: request_watchlist_status()
    Watchlist->>MR: read(watchlist_memory)
    Watchlist-->>Advisor: Watchlist Status

    Note over Advisor: Build candidate list (deterministic)

    Advisor->>Research: request_events(candidates)
    Research-->>Advisor: Stock-level Events

    Note over Advisor: Score candidates (deterministic)

    Advisor->>MR: read(decision_memory, recent)
    MR-->>Advisor: Recent recommendations

    Note over Advisor: Generate narrative (LLM)

    Advisor->>MR: write(decision_memory, today_report)
    Advisor-->>User: Morning Report
```

## Invariants (Must Always Hold)

1. **No layer-skipping.** An Agent in the Agent Layer cannot call a Tool in the Tool Layer that bypasses the Component Layer and directly accesses the Data Layer. All persistence goes through MemoryRepository.

2. **Structured inter-Agent communication.** No Agent receives unstructured text from another Agent and is expected to parse meaning from it. All inter-Agent data is typed and validated.

3. **Advisor is the sole orchestrator.** Only the Advisor Agent initiates multi-step workflows. Specialist Agents respond to requests; they do not self-trigger.

4. **Degradation over failure.** When a layer below fails, the layer above receives a degradation signal ！ not an exception. The system continues with reduced capability rather than stopping.

## Configuration & Environment

All configuration is externalized. No secrets, API keys, or environment-specific values are hardcoded.

- **Environment variables**: API keys, database path, log level, LLM provider
- **Configuration file** (`config.yaml` or `.env`): Agent weights, scoring thresholds, schedule timing
- **Code constants**: Only values that are definitionally constant (e.g., `SHANGHAI_COMPOSITE_INDEX_CODE = "000001"`)

## Technology Stack (V1)

| Component | Technology | Rationale |
|---|---|---|
| Language | Python 3.11+ | LangGraph ecosystem, AkShare/TuShare support, rapid prototyping |
| Database | SQLite (via aiosqlite or sqlite3) | Zero-config, single-user, embedded ！ perfect for a personal tool |
| LLM Provider | DeepSeek API (OpenAI-compatible) | Model-agnostic: works with GPT, Claude, or local models |
| Data | AkShare (primary), TuShare (fallback) | Free, active maintenance, A-share coverage |
| Orchestration | Python native (V1), LangGraph (V2, Phase 12+) | Start simple, adopt framework when complexity demands it |
| Logging | Python `logging` with structured output (JSON Lines) | Debuggable, machine-parseable, standard library |

