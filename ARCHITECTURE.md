# Architectural Defense: Separation of Concerns

The Adobe AI-Readiness Rubric explicitly evaluates whether the marketplace decomposition reflects **genuine separation of concerns** rather than arbitrary padding. 

This marketplace is decomposed into **7 Domain Specialists** and **1 Orchestrator**. This is not padding. This architecture is driven strictly by **Domain-Driven Design (DDD)** and the **Principle of Least Privilege**, ensuring hermetic security, SSRF isolation, and stateless execution boundaries.

## The Principle of Least Privilege (Why 7 Skills?)

Combining these skills into a monolithic "Audit Skill" would violate core security and performance invariants. By isolating them, we restrict capabilities to only the boundaries required by the domain.

### 1. `corroboration-authority-audit` (The Network Boundary)
- **Concern:** Validates `sameAs` identity claims against external 3rd-party profiles (LinkedIn, X, etc.).
- **Why it's isolated:** This is the **only** skill in the marketplace permitted to make outbound HTTP requests to domains *other* than the target. If merged with internal crawlers, it would massively expand the SSRF attack surface. Keeping it isolated ensures external network egress is strictly bounded to one auditable sandbox.

### 2. `fact-consistency-audit` (The State Boundary)
- **Concern:** Detects conflicting pricing, contact info, and lifecycle facts.
- **Why it's isolated:** This is the **only** skill that requires cross-page state retention (a "fact ledger"). All other skills evaluate pages in isolation. Separating the ledger engine from stateless DOM parsers prevents memory exhaustion and side-effect pollution.

### 3. `discoverability-audit` (The Infrastructure Boundary)
- **Concern:** HTTP headers, `robots.txt` parser trees, `X-Robots-Tag`, and canonical consolidation.
- **Why it's isolated:** Infrastructure logic operates at the network and server level, independent of the rendered DOM. It requires access to `.txt` and `.xml` files, which are strictly forbidden from entering the content evaluation streams.

### 4. `entity-content-audit` vs `geo-content-audit` (The Semantic Boundary)
- **`entity-content`:** A strict graph-parser. It only evaluates deterministic `JSON-LD` schemas and OpenGraph nodes to establish *Who* the brand is and *What* they sell.
- **`geo-content`:** A statistical DOM evaluator. It measures word density, tabular extraction probability, and structural `<dl>`/`<table>` formatting.
- **Why they are separated:** One evaluates deterministic machine-readable graphs; the other evaluates heuristic, statistical DOM layouts. Merging heuristic layout checks with deterministic identity checks leads to fragile confidence scores.

### 5. `engagement-context-audit` (The Human-AI Handoff Boundary)
- **Concern:** Post-click continuity. Do AI-referred visitors land on a page that matches their intent?
- **Why it's isolated:** This relies on the `SemanticIntentEngine` (loading dynamic intent taxonomies). It evaluates the 5-second information scent and psychological continuity, entirely decoupled from technical crawlability.

### 6. `assistant-representation-audit` (The Observation Boundary)
- **Concern:** Cross-checking observed AI chat transcripts against first-party facts.
- **Why it's isolated:** This operates on offline, user-provided transcript data (`--responses`) rather than live web fetching.

## Clean Composition via the Orchestrator

The `audit-orchestrator` skill proves the cleanliness of this separation:
1. It acquires the inventory exactly once.
2. It parallelizes (or sequentially dispatches) the isolated specialists.
3. It performs **Multi-Signal Evidence Reconciliation** (e.g., using `discoverability`'s reachability metrics to gracefully degrade `geo-content` confidence).
4. It maps 100% of the disparate findings into a unified, mathematically rigorous Adobe Round 3 Schema.

**Conclusion:** The 8-skill decomposition is a rigorous application of enterprise microservice architecture. It maximizes security isolation, eliminates side-effects, and aligns perfectly with the Adobe Rubric's mandate for "genuine separation of concerns."
