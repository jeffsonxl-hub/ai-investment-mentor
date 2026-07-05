# ADR-003: Hybrid Memory Strategy

## Status
Accepted

## Context

The system needs to remember three types of information: user preferences (watchlist), market conditions over time (market snapshots), and past recommendations (decisions). Two fundamental questions arise:

1. **Who controls what goes into memory?** Should the system automatically manage all memory, or should the user have control over some memory types?

2. **How sophisticated should memory retrieval be?** Should we use vector embeddings and semantic search (RAG) from day one, or start with simple SQL queries?

The trade-off: agentic control is convenient but risks accumulating noise. Human control ensures quality but adds friction. RAG is powerful for unstructured recall but adds significant complexity (embedding models, vector databases, chunking strategies).

## Decision

We adopt a **Hybrid Memory Strategy** with three principles:

1. **Watchlist Memory is human-curated.** The Watchlist Agent recommends additions and removals, but the user must explicitly confirm. The watchlist represents what the user *actually* cares about, not what the AI thinks they should care about.

2. **Market Memory is system-managed.** Market snapshots are written automatically every day. No user involvement needed ¡ª this is pure operational data.

3. **Decision Memory is system-written, human-reviewed (V2).** The system records every recommendation automatically. In V2, the user can provide feedback (confirmed/rejected), and the system learns from it. In V1, decisions are recorded but feedback is deferred.

4. **SQL queries, not vector search.** V1 uses straightforward SQL lookups: "what did we recommend in the last 5 days?" and "which stocks did the user reject?" These are deterministic, fast, and debuggable. RAG is a V2 consideration ¡ª we need enough historical data to justify the complexity, and we need to be sure what retrieval patterns actually matter before embedding anything.

## Consequences

**What becomes easier:**
- **Predictable behavior.** SQL queries return exactly what you ask for. No "approximate nearest neighbor" surprises
- **Zero additional infrastructure.** SQLite ships with Python. No vector database, no embedding pipeline, no index maintenance
- **User trust.** The watchlist is never modified without the user knowledge. They control what they track

**What becomes harder:**
- **Pattern discovery across recommendations.** "Find all past recommendations where the thesis was similar to this one" requires semantic search (RAG). SQL cannot do this
- **Unstructured recall.** If a user asks "what did you say about new energy stocks last month?", SQL can find decisions with stock codes but not decisions *about* a theme
- **Watchlist bootstrapping.** A new user with an empty watchlist gets less personalized results until they curate their list

## Alternatives Considered

### Alternative A: Fully automated memory
The system manages everything. Watchlist auto-populates from top-scoring candidates. Rejected because it removes the user from their own investment process ¡ª the system becomes a black box rather than a teaching tool.

### Alternative B: RAG from day one
Embed all decisions, market snapshots, and news events for semantic search. Rejected for V1 because: (a) RAG adds 3¨C4 new dependencies (embedding model, vector store, chunking, retrieval pipeline), (b) we do not have enough data yet to justify it, and (c) it is harder to debug. We will revisit RAG in Phase 14+ when we have a meaningful decision history.

### Alternative C: LangGraph Checkpointing for all memory
Use LangGraph built-in persistence for everything. Rejected because: (a) LangGraph is not introduced until Phase 12, (b) it couples memory to the orchestration framework, and (c) SQLite gives us more control over schema and queries.
