# Severity & Confidence Calibration Model

This document specifies the rules for assigning severity and confidence scores to audit findings.

---

## Severity Rubric

Severity reflects the direct impact of a defect on AI discovery, knowledge extraction, and visitor retention.

| Severity | Criteria | Examples |
| :--- | :--- | :--- |
| `critical` | **Total Exclusion / Hard Outage**: Prevents AI retrieval engines from crawling or indexing public content. | • `Disallow: /` for AI search retrieval crawlers (`OAI-SearchBot`, `PerplexityBot`).<br>• `<meta name="robots" content="noindex">` on landing page.<br>• HTTP 5xx/4xx on root URL. |
| `high` | **Material Retrieval / Factual Degradation**: Directly leads to corrupted facts, omitted products, or severe rendering extraction failure. | • Core text missing from initial HTML (< 30 words in SPA container).<br>• Conflicting prices published for the same product across first-party pages.<br>• AI assistant quotes wrong pricing due to ambiguous markup.<br>• WAF blocking crawler User-Agents. |
| `medium` | **Corroboration & Orientation Degradation**: Degrades entity clarity, navigation, or cross-web trust anchors. | • Broken `sameAs` authority profile URLs (HTTP 404).<br>• No machine-explicit Organization identity.<br>• Content page lacks `<h1>` or internal navigation menus.<br>• Copyright years vary significantly across site pages. |
| `low` | **Extractability Polish & Minor Signal Gaps**: Minor improvements that make fact extraction easier but do not block ingestion. | • Incomplete Product schema attributes (e.g. missing sku).<br>• Low-information H1 heading (e.g. "Welcome").<br>• Missing dateModified timestamps on static pages. |
| `info` | **Observational & Governance Signals**: Deliberate business choices or observational facts that are explicitly NOT site defects. | • robots.txt blocks training-only crawlers (intentional training opt-out).<br>• Brand mentioned without a direct citation link. |

---

## Confidence Model

Confidence reflects the strength and verifiability of the supporting evidence.

| Confidence | Evidence Quality | Action Rule |
| :--- | :--- | :--- |
| `high` | **Deterministic Direct Probe (L1 Evidence)**: Derived from exact HTTP status codes, verbatim robots.txt rules, DOM text extraction, or parsed JSON-LD structures. | Eligible for all severity levels (`critical`, `high`, `medium`, `low`). |
| `medium` | **Corroborated Heuristic (L2 Evidence)**: Derived from cross-page comparison, text word counts, or multi-probe behavioral analysis. | Eligible for `medium` or `low` severity; `high` severity requires explicit corroborating evidence. |
| `low` | **Weak / Inconclusive Signal (L3 Evidence)**: Speculative or single-sample heuristic lacking secondary corroboration. | **Demoted by the Eligibility Gate** to a proactive recommendation (`proactive_actions[]`); never asserted as a critical/high defect. |

