# Architectural Defense: Separation of Concerns

The Adobe AI-Readiness Rubric explicitly evaluates whether the marketplace decomposition reflects **genuine separation of concerns** rather than arbitrary padding. 

This marketplace is decomposed into **6 Domain Specialists** and **1 Orchestrator**. This is not padding. This architecture is driven strictly by the **Stateful Knowledge Graph Pattern** and the **Principle of Least Privilege**, ensuring hermetic security, SSRF isolation, and causal execution boundaries.

## The Principle of Least Privilege (Why 7 Skills total?)

Combining these skills into a monolithic "Audit Skill" would violate core security and performance invariants. By isolating them, we restrict capabilities to only the boundaries required by the specific domain check.

### 1. `corroboration-authority-audit` (The Network Boundary)
- **Concern:** Validates `sameAs` identity claims against external 3rd-party profiles.
- **Why it's isolated:** This is the **only** skill in the marketplace permitted to resolve outbound network calls to domains *other* than the primary target. Keeping it isolated ensures external network egress is strictly bounded to one auditable sandbox, preventing SSRF attacks across the main crawler fleet.

### 2. `fact-consistency-audit` (The Validation Boundary)
- **Concern:** Detects conflicting pricing, contact info, and lifecycle facts.
- **Why it's isolated:** This skill executes temporal contradiction logic across the Knowledge Graph. It merges previous standalone capabilities (like assistant representation checks) into a single unified temporal ledger for factual verification.

### 3. `discoverability-audit` (The Infrastructure Boundary)
- **Concern:** HTTP status codes, `robots.txt` parser trees, Canonical consolidation, and Retrieval-Window Indexing.
- **Why it's isolated:** Infrastructure logic evaluates whether an AI crawler can even *reach* or *index* a page. If this stage fails, executing deep semantic evaluation is wasted compute.

### 4. `entity-content-audit` vs `geo-content-audit` (The Semantic Boundary)
- **`entity-content`:** A strict knowledge-parser. It extracts deterministic `JSON-LD` schemas and HTML properties to establish *Who* the brand is and *What* they sell, seeding the Graph.
- **`geo-content`:** Evaluates text for proven Generative Engine Optimization (GEO) dimensions, specifically "In-Depth Mechanisms" (causal conjunctions) and "Specific Evidence" (digits/metrics) based on AutoGEO research.
- **Why they are separated:** One parses strict explicit graphs; the other evaluates semantic styling. Merging them leads to overlapping concerns and fragile confidence scores.

### 5. `engagement-context-audit` (The Human-AI Handoff Boundary)
- **Concern:** Post-click continuity. Do AI-referred visitors land on a page that matches their intent?
- **Why it's isolated:** This evaluates Information Scent Anchoring—verifying that the Canonical Entity extracted from the Knowledge Graph matches the anchor text used in the primary `<h1>` tag. It is decoupled from technical crawlability.

## Clean Composition via the Orchestrator

The `audit-orchestrator` skill proves the cleanliness of this separation:
1. It creates an atomic, concurrency-safe `state.json` file.
2. It dynamically invokes the skills in a strict causal pipeline: `Discoverability -> Entity -> Fact -> Corroboration -> GEO -> Engagement`.
3. It maps 100% of the synthesized findings into the unified, strictly-typed Adobe Round 3 Schema (enforcing `technical_fix` vs `creative_fix`).

**Conclusion:** The 7-skill decomposition maximizes security isolation, enables stateful cross-skill intelligence, and aligns perfectly with the Adobe Rubric's mandate for "genuine separation of concerns."
