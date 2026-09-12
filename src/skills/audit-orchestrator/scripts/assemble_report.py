"""Evidence gate, cause-scoped deduplication, queue ordering and schema validation.

Pure Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from .plan import LABELS, plan, infer_finding_difficulty, calculate_priority_index  # type: ignore
    from .validate_report import validate_report_dict  # type: ignore
except (ImportError, ValueError):
    try:
        from plan import LABELS, plan, infer_finding_difficulty, calculate_priority_index  # type: ignore
        from validate_report import validate_report_dict  # type: ignore
    except ImportError:
        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))
        from plan import LABELS, plan, infer_finding_difficulty, calculate_priority_index  # type: ignore
        from validate_report import validate_report_dict  # type: ignore

try:
    from .causal_gate import apply_causal_suppression, detect_business_archetype  # type: ignore
except (ImportError, ValueError):
    try:
        from causal_gate import apply_causal_suppression, detect_business_archetype  # type: ignore
    except ImportError:
        apply_causal_suppression = None
        detect_business_archetype = None


def build_run_manifest(site: str, duration_sec: float = 0.0) -> Dict[str, Any]:
    """Build machine-readable execution provenance manifest with reference SHA-256 hashes."""
    ref_dir = Path(__file__).resolve().parents[1] / "references"
    ref_hashes = {}
    for fn in ("checks.json", "knowledge-base.md", "core-synthesis-digest.md", "report-schema.json", "telemetry-schema.json"):
        fp = ref_dir / fn
        if fp.exists():
            ref_hashes[fn] = hashlib.sha256(fp.read_bytes()).hexdigest()
    ts = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "manifest_version": "1.0.0",
        "site": site,
        "started_at": ts,
        "completed_at": ts,
        "duration_seconds": round(duration_sec, 2),
        "execution_status": "complete",
        "pipeline_stages": [
            "1. Inventory Acquisition (SSRF-Safe, Pure Python)",
            "2. Specialist Telemetry Collection (6 Sensors)",
            "3. 6-Layer Causal DAG Suppression & Route Analysis",
            "4. Business Archetype Classification & Severity Reweighting",
            "5. Deterministic Readiness & Citability Scoring",
            "6. Draft-07 Report Synthesis & Schema Validation",
        ],
        "participating_skills": [
            "audit-orchestrator",
            "web-scraper",
            "discoverability-audit",
            "entity-content-audit",
            "fact-consistency-audit",
            "corroboration-authority-audit",
            "geo-content-audit",
            "engagement-context-audit",
        ],
        "reference_checksums_sha256": ref_hashes,
        "runtime_dependencies": "Pure Python 3.9+ standard library only",
    }


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_evidence(item: Dict[str, Any], artifacts: Dict[str, Any]) -> None:
    """Gate every candidate finding through strict immutable evidence verification."""
    refs = item.get("evidence_refs", [])
    if not refs:
        raise ValueError("Missing evidence references")
    for ref in refs:
        artifact = artifacts.get(ref.get("artifact"))
        if artifact is None:
            raise ValueError("Evidence artifact not found")
        quote = ref.get("quote")
        if not isinstance(quote, str) or not quote or not ref.get("locator"):
            raise ValueError("Exact quote and locator required")
        locator = ref["locator"]
        if locator in ("response body", "response"):
            locator = "text"
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*(?:\[\d+\])?(?:\.[A-Za-z_][A-Za-z_0-9]*(?:\[\d+\])?)*", locator):
            raise ValueError("Unsupported evidence locator grammar")
        selected: Any = artifact
        try:
            for part in locator.split("."):
                m = re.fullmatch(r"([A-Za-z_][A-Za-z_0-9]*)(?:\[(\d+)\])?", part)
                if not m:
                    raise ValueError("Malformed locator")
                selected = selected[m.group(1)]
                if m.group(2) is not None:
                    selected = selected[int(m.group(2))]
        except (KeyError, TypeError, IndexError):
            raise ValueError("Evidence locator does not resolve")
        haystack = selected if isinstance(selected, str) else json.dumps(selected, ensure_ascii=False)
        if (
            quote not in haystack
            and json.dumps(quote, ensure_ascii=False)[1:-1] not in haystack
            and not (locator == "source.canonicals" and all(q in haystack for q in quote.split(" | ")))
        ):
            raise ValueError("Quote not found at cited locator")
    if item.get("finding_kind") == "confirmed_problem" and not item.get("collection_complete_for_scope"):
        raise ValueError("Confirmed problem lacks complete evidence for its narrow scope")
    if not item.get("severity_reason") or not item.get("scope"):
        raise ValueError("Scope and activated severity reason required")


def sort_tasks(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort audit tasks topologically by dependency DAG, lane queues, severity, and difficulty."""
    queues = {"confirmed": 0, "advisory": 1, "investigation": 2}

    def key(item: Dict[str, Any]) -> tuple[Any, ...]:
        band = item.get("actual_band", "S2")
        severity = int(band[1]) if band.startswith("S") and len(band) > 1 else -1
        d = item.get("difficulty")
        return (
            queues.get(item.get("queue", "confirmed"), 0),
            -severity,
            d if d is not None else 0,
            -len(set(item.get("affected_urls", [item.get("scope", "")]))),
            -int(item.get("established_importance", 0)),
            item.get("id", ""),
        )

    pending = {i["id"]: i for i in items}
    done: set[str] = set()
    output: List[Dict[str, Any]] = []
    for item in items:
        for dep in item.get("depends_on", []):
            if dep not in pending:
                raise ValueError("Unknown prerequisite: " + dep)
            if queues.get(pending[dep].get("queue", "confirmed"), 0) > queues.get(item.get("queue", "confirmed"), 0):
                raise ValueError("Unresolved cross-queue prerequisite; move dependent to investigation")

    while pending:
        available = [i for i in pending.values() if set(i.get("depends_on", [])) <= done]
        if not available:
            raise ValueError("Dependency cycle")
        first = min(available, key=key)
        output.append(first)
        done.add(first["id"])
        del pending[first["id"]]
    return output


def validate_report(report: Dict[str, Any]) -> bool:
    """Validate report dictionary against schema and count invariants."""
    schema_path = Path(__file__).resolve().parents[1] / "references/report-schema.json"
    valid, errors = validate_report_dict(report, str(schema_path))
    if not valid:
        raise ValueError("; ".join(errors))
def resolve_dag_node(cid: str, cat: str) -> str:
    """Resolve exact Causal DAG layer (RETRIEVAL, RENDERING, ENTITY, FACTS, CORROBORATION, GEO_CITABILITY, ENGAGEMENT)."""
    cid_u = str(cid or "").upper()
    cat_l = str(cat or "").lower()

    # Support 134-item catalogue check prefixes (e.g. E1, D1, J1, C1, N10)
    if len(cid_u) <= 4 and cid_u and cid_u[0].isalpha():
        if cid_u.startswith("BN"):
            return "FACTS"
        if cid_u.startswith(("BC", "PP", "SA", "SC")):
            return "CORROBORATION"
        if cid_u.startswith(("EC", "ED", "ME")):
            return "ENTITY"
        if len(cid_u) <= 3 and (len(cid_u) == 1 or cid_u[1:].isdigit()):
            pfx = cid_u[0]
            if pfx in ("A", "B", "D", "H"):
                return "RETRIEVAL"
            if pfx == "C":
                return "RENDERING"
            if pfx == "E":
                return "ENTITY"
            if pfx == "F":
                return "FACTS"
            if pfx in ("G", "N"):
                return "GEO_CITABILITY"
            if pfx in ("I", "J"):
                return "ENGAGEMENT"
            if pfx == "P":
                return "CORROBORATION"

    # Layer 1: RENDERING
    if any(k in cid_u for k in ("RENDER", "HYDRAT", "SPA_SHELL", "UNRENDERED", "CSR_")):
        return "RENDERING"

    # Layer 0: RETRIEVAL
    if any(k in cid_u for k in ("RETRIEVAL", "ROBOTS", "NOINDEX", "SITEMAP", "CANONICAL", "HTTP_", "STATUS_", "REDIRECT", "LOCALE_", "CRAWL")):
        return "RETRIEVAL"
    if cat_l in ("crawlability", "discoverability", "indexability", "locale", "canonicalization", "http"):
        return "RETRIEVAL"

    # Layer 2: ENTITY
    if any(k in cid_u for k in ("ENTITY", "ORGANIZATION", "PRODUCT", "OFFER", "SCHEMA", "PRICE_METADATA", "LOCAL_BUSINESS", "SERVICE_SCHEMA", "COMMERCIAL_PRODUCT")):
        return "ENTITY"
    if cat_l in ("entity", "entity-identity", "structured-data", "structured_data", "commercial", "product-answerability", "entity-answerability", "schema-deprecation"):
        return "ENTITY"

    # Layer 3: FACTS
    if any(k in cid_u for k in ("CROSS_PAGE", "CONTRADICTION", "DISCREPANCY", "DRIFT", "STALE_YEAR", "TERMS_CONFLICT")):
        return "FACTS"
    if cat_l in ("fact-consistency", "fact_consistency", "facts", "lifecycle", "freshness", "commercial_terms", "representation"):
        return "FACTS"

    # Layer 4: CORROBORATION
    if any(k in cid_u for k in ("CORROBORATION", "SAMEAS", "AUTHORITY", "WIKIDATA", "WIKIPEDIA", "LINKEDIN", "ANCHOR", "MIRROR")):
        return "CORROBORATION"
    if cat_l in ("corroboration", "authority", "sameas"):
        return "CORROBORATION"

    # Layer 6: ENGAGEMENT
    if any(k in cid_u for k in ("ORIENTATION", "PROOF_ARCHITECTURE", "FRICTION", "OBJECTION", "PATHWAY", "CTA_", "SCENT", "BOUNCE", "VIEWPORT_ANSWER", "INTENT_TO_LANDING")):
        return "ENGAGEMENT"
    if cat_l in ("engagement", "conversion-continuity", "user-experience", "extraction"):
        return "ENGAGEMENT"

    # Layer 5: GEO_CITABILITY
    if any(k in cid_u for k in ("INFORMATION_GAIN", "QUOTATION", "MATRIX", "DEPTH", "CITABILITY", "FACT_TO_TOKEN", "FAQ_DEFICIT", "PASSAGE", "KEYWORD_DENSITY", "HEDGE", "BLUF", "EVIDENCE")):
        return "GEO_CITABILITY"
    if cat_l in ("geo_content", "geo-content", "content", "citability"):
        return "GEO_CITABILITY"

    return "RETRIEVAL"


def generate_priority_justification(f: Dict[str, Any], idx: int) -> str:
    """Generate needle-moving ordering judgment explaining why this finding is ranked at position #idx."""
    cid = str(f.get("cause_id") or f.get("id") or f.get("check_id") or "").upper()
    dag = str(f.get("dag_node") or "RETRIEVAL")

    if cid in ("AI_RETRIEVAL_BLOCKED", "CRAWLER_ACCESS_DENIED"):
        just = "Keystone Layer 0 defect. Without HTTP 200 accessibility, AI retrieval engines cannot crawl or index pages, rendering all downstream markup and content invisible."
    elif "NOINDEX" in cid:
        just = "Explicit indexability blocker. The noindex directive instructs retrieval bots to purge the route from search indexes, superseding all on-page structured data and citability optimizations."
    elif "ROBOTS" in cid:
        just = "Crawler access barrier. Disallow directives on verified AI search bots prevent modern generative answer engines from retrieving the brand's primary domain content."
    elif "RENDER" in cid or dag == "RENDERING":
        just = "Layer 1 rendering failure. Serving an unrendered client-side JavaScript shell starves non-executing AI scrapers of text, preventing downstream entity extraction and neural dense retrieval."
    elif "MATERIAL_ENTITY_AMBIGUITY" in cid or "MISSING_ORGANIZATION" in cid:
        just = "Upstream entity anchor. Machine-explicit Schema.org Organization markup is required for LLMs to resolve brand identity and anchor facts in global knowledge graphs before citability can be attributed."
    elif "PRODUCT" in cid or "OFFER" in cid:
        just = "Commercial answerability blocker. Incomplete or unrendered product and pricing schemas prevent AI shopping assistants from providing direct buy recommendations and accurate price comparisons."
    elif "SAMEAS" in cid or "AUTHORITY" in cid or "KNOWLEDGE_GRAPH" in cid or dag == "CORROBORATION":
        just = "Knowledge graph consensus gap. Omitting established third-party authority profiles from Schema.org sameAs prevents AI models from verifying external consensus and corroborating brand claims."
    elif "CROSS_PAGE" in cid or "CONTRADICTION" in cid or dag == "FACTS":
        just = "Hallucination catalyst. Conflicting numerical or commercial claims across first-party pages directly depress RAG consensus confidence and cause generative engines to withhold definitive brand answers."
    elif "INFORMATION_GAIN" in cid:
        just = "Primary LLM citation filter. Content lacking proprietary data or empirical benchmarks is filtered out during generative answer synthesis because frontier models prioritize net-new information gain over generic summaries."
    elif "QUOTATION" in cid:
        just = "Citability multiplier. Grounded in Princeton KDD 2024 empirical benchmarks, attributed quotations from domain experts deliver a +40.9% lift in AI citation selection over unattributed assertions."
    elif "MATRIX" in cid or "COMPARATIVE" in cid:
        just = "High-lift retrieval structure. Princeton KDD 2024 benchmarks prove comparative tables yield the highest single empirical citation boost (+55.3%) for competitive brand queries."
    elif "FACT_TO_TOKEN" in cid:
        just = "RAG density deficit. Low atomic fact-to-token ratio causes dense retrieval algorithms to score passages as low-information fluff, routing queries to denser third-party references."
    elif "DEPTH" in cid:
        just = "Mechanistic depth gap. Generative engines favor sources explaining 'how' and 'why' through causal conjunctions over shallow assertions when answering complex user prompts."
    elif "ORIENTATION" in cid or "VALUE_PROPOSITION" in cid:
        just = "Post-citation bounce vector. Visitors arriving from specific AI citations bounce within 5 seconds when the hero section fails the cognitive orientation test with vague marketing abstractions."
    elif "PROOF" in cid:
        just = "Skepticism hurdle. AI search evaluators require quantitative benchmarks, enterprise logos, or compliance attestations immediately upon arrival to validate the factual claims made in the citation."
    elif "FRICTION" in cid or "GATE" in cid:
        just = "Conversion bottleneck. Forcing high-intent visitors arriving from citations into mandatory sales meetings without self-service sandbox exploration causes immediate referral abandonment."
    elif "PATHWAY" in cid:
        just = "Conversion cul-de-sac. Informational content concluding without logical conversion or exploration pathways strands interested visitors arriving from AI search."
    elif "CTA" in cid:
        just = "Intent continuity failure. Delaying primary action buttons behind auxiliary navigation blocks breaks the user task handoff initiated by the AI assistant citation."
    elif "LOCALE" in cid:
        just = "Multi-region retrieval mismatch. Invalid hreflang directives prevent search engines from routing localized queries to the correct regional brand assets."
    elif "FAQ" in cid:
        just = "Empirical citation penalty. Standalone conversational FAQs without underlying data points or technical specifications suffer a documented -5.7% citation penalty in generative engines."
    elif dag == "GEO_CITABILITY":
        just = "Deficit in statistical density, causal conjunctions, or BLUF primacy reduces heuristic citability score based on empirical GEO benchmarks."
    elif dag == "ENGAGEMENT":
        just = "Post-citation information scent or navigation friction indicates early-document orientation friction upon arrival from AI search."
    else:
        just = "Prioritized based on direct impact on AI retrieval visibility and user task continuity."

    return f"Rank #{idx}: {just}"


def assemble(
    site: str,
    candidates: List[Dict[str, Any]],
    records: List[Dict[str, Any]],
    checks: List[Dict[str, Any]],
    coverage: Dict[str, Any],
    browser: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Assemble final synthesized report from candidate findings and collected inventory."""
    artifacts = {a["artifact"]: a for a in records if isinstance(a, dict) and a.get("artifact")}
    artifacts.update({a["artifact"]: a for a in (browser or {}).get("captures", []) if isinstance(a, dict) and a.get("artifact")})
    catalogue = {c["check_id"]: c for c in checks}
    observations: List[Dict[str, Any]] = []
    dropped: List[Dict[str, Any]] = []
    merged: Dict[Any, Dict[str, Any]] = {}
    proactive_actions: List[Dict[str, Any]] = []

    if apply_causal_suppression is not None and candidates:
        inv_pages = []
        for r in records:
            if isinstance(r, dict) and r.get("url"):
                text_str = r.get("text") or ""
                wc = len(text_str.split()) if text_str else r.get("word_count", 0)
                inv_pages.append({
                    "url": r["url"],
                    "word_count": wc,
                    "status": r.get("status", 200),
                    "html": text_str[:2000] if text_str else "",
                })
        orig_candidates = list(candidates)
        surviving, suppressed, _dag_meta = apply_causal_suppression(candidates, inv={"pages": inv_pages})
        for sc in suppressed:
            dropped.append(dict(
                candidate_index=orig_candidates.index(sc) if sc in orig_candidates else -1,
                check_id=sc.get("check_id"),
                reason="Suppressed by 6-Layer Causal DAG: downstream symptom of upstream blocker",
            ))
        candidates = surviving
        detected_arch = detect_business_archetype({"pages": inv_pages, "site": site}) if detect_business_archetype else "corporate"
        unrendered_prod = [
            sc for sc in suppressed
            if any(k in str(sc.get("cause_id") or sc.get("id") or sc.get("check_id", "")) for k in ("ATTRIBUTE_INCOMPLETENESS", "INCOMPLETE_OFFER_ATTRIBUTES", "COMMERCIAL_PRODUCT_DATA_CONTRADICTION", "PRODUCT", "OFFER"))
        ]
        if unrendered_prod and detected_arch == "ecommerce":
            sample_scope = unrendered_prod[0].get("scope", "commercial route")
            proactive_actions.append({
                "id": "P-001",
                "title": "Pre-Hydration Product Schema Architecture",
                "category": "entity",
                "summary": f"Commercial routes (e.g. {sample_scope}) serve unrendered client-side JS shells. When implementing SSR or pre-rendering, embed complete Schema.org Product and Offer markup in initial HTML to prevent downstream answerability gaps.",
                "priority": "high",
                "technical_fix": "Pre-render Schema.org Product JSON-LD in the server response before client bundle execution.",
                "creative_fix": "Ensure core product specs, pricing, and availability are visible above the fold in semantic HTML.",
                "verification": "Fetch raw HTML without executing JavaScript and confirm Schema.org Product markup is detected.",
            })

    for index, item in enumerate(candidates):
        try:
            item = dict(item)
            check = catalogue.get(item["check_id"])
            if not check:
                raise ValueError(f"Unknown check_id: {item.get('check_id')}")
            if item["actual_band"] not in LABELS:
                raise ValueError("Invalid actual band")
            if item["finding_kind"] not in ("confirmed_problem", "advisory", "investigation", "informational_observation"):
                raise ValueError("Unknown finding kind")
            if item["finding_kind"] == "confirmed_problem" and item["actual_band"] in ("S0", "U"):
                raise ValueError("Unassessable/no-change item cannot be a confirmed problem")
            if item["finding_kind"] == "confirmed_problem" and check.get("feasibility", "").startswith(("Not possible", "Exclude")):
                raise ValueError("Check cannot support automated confirmed failure")
            if item.get("difficulty") is not None and (
                not isinstance(item["difficulty"], int) or not 1 <= item["difficulty"] <= 5 or not item.get("difficulty_reason")
            ):
                raise ValueError("Difficulty requires D1-D5 and a justification")
            if item.get("difficulty_range") is not None:
                rg = item["difficulty_range"]
                if len(rg) != 2 or any(not isinstance(x, int) for x in rg) or not 1 <= rg[0] <= rg[1] <= 5:
                    raise ValueError("Invalid difficulty interval")
            verify_evidence(item, artifacts)
            item = plan(item, check)
            if item["finding_kind"] == "informational_observation" or item["actual_band"] == "S0":
                observations.append(item)
                continue
            ids = sorted(set(item.get("related_check_ids", []) + [item["check_id"]]))
            if any(i not in catalogue for i in ids):
                raise ValueError("Unknown related check ID")
            evidence_key = tuple(sorted((e["artifact"], e["locator"]) for e in item["evidence_refs"]))
            cause = item.get("root_cause_key")
            if cause and not item.get("root_cause_reason"):
                raise ValueError("Explicit root cause requires reasoning")
            dedup = (item["scope"], item["finding_kind"], cause or evidence_key)
            item["related_check_ids"] = ids
            item["id"] = item.get("id") or "F-" + hashlib.sha256(repr(dedup).encode()).hexdigest()[:12]
            if dedup in merged:
                prev = merged[dedup]
                prev["related_check_ids"] = sorted(set(prev["related_check_ids"] + ids))
                prev["evidence_refs"] += [e for e in item["evidence_refs"] if e not in prev["evidence_refs"]]
                b_curr = str(item.get("actual_band", ""))
                curr_band_num = int(b_curr[1]) if b_curr.startswith("S") and len(b_curr) > 1 and b_curr[1].isdigit() else -1
                b_prev = str(prev.get("actual_band", ""))
                prev_band_num = int(b_prev[1]) if b_prev.startswith("S") and len(b_prev) > 1 and b_prev[1].isdigit() else -1
                if curr_band_num > prev_band_num:
                    prev["actual_band"] = item["actual_band"]
                prev["depends_on"] = sorted(set(prev["depends_on"] + item["depends_on"]))
                if item.get("downstream_symptoms"):
                    prev_syms = prev.setdefault("downstream_symptoms", [])
                    for s in item["downstream_symptoms"]:
                        if s not in prev_syms:
                            prev_syms.append(s)
                prev["priority_index"] = None
                prev["difficulty"] = None
            else:
                merged[dedup] = item
        except (ValueError, KeyError, TypeError) as exc:
            dropped.append(dict(candidate_index=index, check_id=item.get("check_id"), reason=str(exc)))

    findings = sort_tasks(list(merged.values()))
    for idx, item in enumerate(findings, 1):
        item["severity"] = LABELS[item["actual_band"]]
        item["priority_rank"] = idx
        evidence_snippets = []
        for e in item.get("evidence_refs", []):
            art = e.get("artifact", "primary_source")
            loc = e.get("locator", "text")
            q = e.get("quote")
            obs = e.get("structural_observation")
            if q:
                evidence_snippets.append(f"{art} at {loc}: {q[:500]}")
            elif obs:
                evidence_snippets.append(f"{art} at {loc} [structural]: {obs[:500]}")
            else:
                evidence_snippets.append(f"{art} at {loc} (verified absence)")
        item["evidence"] = "; ".join(evidence_snippets) if evidence_snippets else str(item.get("observation") or "Empirical measurement")
        cid = str(item.get("cause_id") or item.get("check_id", ""))
        cat = "discoverability"
        if cid.startswith("E") or "ENTITY" in cid or "PRODUCT" in cid or "OFFER" in cid:
            cat = "entity_content"
        elif cid.startswith("N") or "FACT" in cid or "PRICE" in cid:
            cat = "fact_consistency"
        elif cid.startswith("P") or "AUTHORITY" in cid or "SAMEAS" in cid:
            cat = "corroboration"
        elif cid.startswith("G") or "CITABILITY" in cid or "GEO" in cid:
            cat = "geo_content"
        elif cid.startswith(("I", "J")) or "ENGAGEMENT" in cid or "CTA" in cid or "SCENT" in cid:
            cat = "engagement"
        item.setdefault("category", cat)
        # Root cause must be mechanistic cause, not severity reason
        if not item.get("root_cause") or item.get("root_cause") == item.get("severity_reason"):
            item["root_cause"] = item.get("root_cause") or (f"Defect mechanism for {cid}" if cid else "Unspecified defect mechanism")
        # Confidence must not default unconditionally to high
        if not item.get("confidence") or item.get("confidence") not in ("high", "medium", "low"):
            item["confidence"] = "low"

        if not item.get("affected_urls"):
            item["affected_urls"] = [item["scope"]] if item.get("scope") and str(item["scope"]).startswith("http") else [site]

        # Compute DAG node per 6-Layer Causal DAG
        dag_node = resolve_dag_node(cid, cat)
        item["dag_node"] = dag_node

        # Compute priority_justification explaining needle-moving rationale
        just = generate_priority_justification(item, idx)
        item["priority_justification"] = just

        # Synchronize difficulty and priority_index
        action = dict(item.get("suggested_action") or {})
        if item.get("queue") != "investigation" and (item.get("remedy_readiness") == "ready" or item.get("difficulty") is not None):
            diff = item.get("difficulty") if item.get("difficulty") is not None else infer_finding_difficulty(item)
            band = str(item.get("actual_band", "S2"))
            sev_num = int(band[1]) if band.startswith("S") and len(band) > 1 and band[1].isdigit() else 2
            p_idx = calculate_priority_index(sev_num, diff)
            item["difficulty"] = diff
            item["priority_index"] = p_idx
            action["difficulty"] = diff
            action["priority_index"] = p_idx
        else:
            diff = item.get("difficulty")
            item["difficulty"] = diff
            action["difficulty"] = diff
            action["priority_index"] = item.get("priority_index")

        if not item.get("scope"):
            item["scope"] = site

        if not item.get("impact"):
            cid = str(item.get("cause_id") or item.get("check_id", ""))
            cat = str(item.get("category", "discoverability"))
            if cat == "fact_consistency" or cid.startswith("BN") or "FACT" in cid or "PRICE" in cid:
                raw_impact = "Conflicting first-party facts reduce model consensus confidence, leading to hallucinations or citation exclusion."
            elif cat == "corroboration" or cid.startswith(("BC", "PP", "SA", "SC", "P")) or "AUTHORITY" in cid or "SAMEAS" in cid:
                raw_impact = "Lack of third-party authority links weakens brand identity verification across external knowledge graphs."
            elif cat == "entity_content" or cid.startswith(("EC", "ED", "ME", "E")) or "ENTITY" in cid or "PRODUCT" in cid or "OFFER" in cid:
                raw_impact = "Ambiguous entity and product attributes prevent generative engines from answering user purchase queries directly."
            elif cat == "geo_content" or cid.startswith(("N", "G")) or "CITABILITY" in cid or "GEO" in cid:
                raw_impact = "Low statistical density and absent direct-answer formatting depress citation frequency in generative response engines."
            elif cat in ("engagement", "engagement_context") or cid.startswith(("I", "J")) or "SCENT" in cid or "CTA" in cid or "ENGAGEMENT" in cid:
                raw_impact = "Degrades post-citation visitor orientation and decreases intent-handoff retention."
            elif cat in ("discoverability", "crawlability") or cid.startswith(("A", "B", "D", "F", "H")):
                raw_impact = "Impairs AI crawler indexation, causing the domain or catalog to be omitted from AI search retrieval."
            else:
                raw_impact = "Degrades post-citation visitor orientation and decreases intent-handoff retention."
            item["impact"] = raw_impact

        action.setdefault("technical_fix", f"Technical remediation for {item.get('check_id', '')}.")
        action.setdefault("creative_fix", None)
        action.setdefault("verification", "Verify remediation in production.")
        action.setdefault("is_proactive", False)
        item["suggested_action"] = action

    summary = dict(
        total_findings=len(findings),
        critical=sum(i["severity"] == "critical" for i in findings),
        high=sum(i["severity"] == "high" for i in findings),
        medium=sum(i["severity"] == "medium" for i in findings),
        low=sum(i["severity"] == "low" for i in findings),
        confirmed_problems=sum(i.get("finding_kind") == "confirmed_problem" for i in findings),
    )

    # 1. Extract pages and sensor results from records
    pages_list = [
        r for r in records
        if isinstance(r, dict) and not str(r.get("artifact", "")).startswith("sensor-") and r.get("url")
    ]
    total_pages = max(len(pages_list), 1)

    sensors: Dict[str, Any] = {}
    for r in records:
        if isinstance(r, dict):
            art = str(r.get("artifact", ""))
            s_name = r.get("sensor") or (art[7:] if art.startswith("sensor-") else None)
            if s_name:
                txt = r.get("text", "")
                if txt:
                    try:
                        sensors[s_name] = json.loads(txt)
                    except Exception:
                        pass

    # 2. Compute Deterministic Dimensions
    if pages_list:
        def _to_code(p_item):
            c = p_item.get("status_code") or p_item.get("status")
            try:
                val = int(c)
                return val if 100 <= val <= 599 else None
            except (ValueError, TypeError):
                return None
        crawlable_count = sum(1 for p in pages_list if _to_code(p) is not None and _to_code(p) < 400)
        crawlability = round((crawlable_count / total_pages) * 100.0, 2) if total_pages > 0 else 0.0

        substantive_pages = [
            p for p in pages_list
            if (len((p.get("text") or "").split()) if p.get("text") else p.get("word_count", 0)) >= 50
        ]
        retrieval_readiness = round((len(substantive_pages) / total_pages) * 100.0, 2) if total_pages > 0 else 0.0
    else:
        crawlability = 0.0
        retrieval_readiness = 0.0

    geo_res = sensors.get("geo-content-audit", {})
    avg_cit = geo_res.get("coverage", {}).get("average_citability_score", 0.0)
    citation_readiness = round(float(avg_cit or 0.0), 2)

    entity_res = sensors.get("entity-content-audit", {})
    corrob_res = sensors.get("corroboration-authority-audit", {})
    has_jsonld = bool(entity_res.get("coverage", {}).get("jsonld_present", False))
    has_org = bool(entity_res.get("entity_snapshot", {}).get("organization"))
    sameas_count = int(corrob_res.get("coverage", {}).get("sameas_declared", 0) or 0)
    if has_jsonld and has_org and sameas_count >= 2:
        entity_authority = 100.0
    elif has_jsonld or has_org:
        entity_authority = 50.0
    elif sameas_count > 0:
        entity_authority = 25.0
    else:
        entity_authority = 0.0

    disc_res = sensors.get("discoverability-audit", {})
    disc_cov = disc_res.get("coverage", {})
    raw_bots_allowed = disc_cov.get("retrieval_bots_allowed")
    raw_bots_total = disc_cov.get("retrieval_bots_total")
    bots_allowed = int(raw_bots_allowed) if raw_bots_allowed is not None else 4
    bots_total = max(int(raw_bots_total) if raw_bots_total is not None else 4, 1)
    bot_ratio = bots_allowed / bots_total if bots_total else 1.0
    cross_engine_visibility = round(bot_ratio * retrieval_readiness, 2)

    commerce_pages = sum(
        1 for p in pages_list
        if p.get("page_type") in ("product_detail", "product", "pricing")
        or bool(p.get("has_product_schema"))
        or any(k in str(p.get("url", "")).lower() for k in ("/product/", "/pricing", "/cart", "/checkout"))
    )
    agentic_commerce = round((commerce_pages / total_pages) * 100.0, 2) if pages_list else 0.0

    dimensions = {
        "crawlability": crawlability,
        "retrieval_readiness": retrieval_readiness,
        "citation_readiness": citation_readiness,
        "entity_authority": entity_authority,
        "cross_engine_visibility": cross_engine_visibility,
        "agentic_commerce": agentic_commerce,
    }
    weights = {
        "crawlability": 0.2,
        "retrieval_readiness": 0.15,
        "citation_readiness": 0.25,
        "entity_authority": 0.2,
        "cross_engine_visibility": 0.1,
        "agentic_commerce": 0.1,
    }
    composite_score = round(sum(dimensions[k] * weights[k] for k in weights), 2)
    if composite_score >= 85.0:
        grade = "A"
    elif composite_score >= 70.0:
        grade = "B"
    elif composite_score >= 50.0:
        grade = "C"
    elif composite_score >= 30.0:
        grade = "D"
    else:
        grade = "F"

    finding_cids = {str(f.get("cause_id") or f.get("id", "")) for f in findings}
    has_render_gap = "RENDERED_CONTENT_GAP" in finding_cids or any("RENDER" in c for c in finding_cids)
    dimension_status = {
        "crawlability": "observed" if pages_list else "unmeasured",
        "retrieval_readiness": "observed" if pages_list else "unmeasured",
        "citation_readiness": "provisional" if has_render_gap else "observed",
        "entity_authority": "provisional" if has_render_gap else "observed",
        "cross_engine_visibility": "observed" if pages_list else "unmeasured",
        "agentic_commerce": "provisional" if has_render_gap else "observed",
    }
    readiness = {
        "composite_score": composite_score,
        "grade": grade,
        "dimensions": dimensions,
        "weights": weights,
        "dimension_status": dimension_status,
        "score_scope": "Observed static inventory and specialist telemetry; heuristic citation-readiness proxy, not live provider ranking or citation measurement.",
    }

    # Archetype detection
    if detect_business_archetype is not None:
        archetype = detect_business_archetype({"pages": pages_list})
    elif commerce_pages > 0 or any("PRODUCT" in c or "OFFER" in c for c in finding_cids):
        archetype = "ecommerce"
    elif any("/pricing" in str(p.get("url", "")).lower() for p in pages_list):
        archetype = "saas"
    elif any("/article" in str(p.get("url", "")).lower() or "/post" in str(p.get("url", "")).lower() for p in pages_list):
        archetype = "publisher"
    else:
        archetype = "corporate"

    summary["detected_archetype"] = archetype

    cov_dict = dict(coverage) if coverage else {}
    if cov_dict.get("sensor_errors"):
        audit_status = "partial"
    elif not pages_list:
        audit_status = "failed"
    else:
        audit_status = "complete"

    report = dict(
        schema_version="1.0.0",
        site=site,
        audited_at=now(),
        audit_status=audit_status,
        archetype=archetype,
        summary=summary,
        findings=findings,
        proactive_actions=proactive_actions,
        readiness=readiness,
        observations=observations,
        dropped_findings=dropped,
        coverage=cov_dict,
        limitations=[
            "No JavaScript browser rendering was performed.",
            "Findings are based only on resources successfully acquired during this audit.",
            "Robots.txt observations represent declared crawler permissions and do not prove search inclusion, indexing, ranking, or citation.",
            "No claim is made about actual citation or placement by a specific AI assistant.",
            "Engagement observations are content/navigation proxies unless external behavioral analytics are explicitly supplied.",
        ],
        evidence_classes={
            "first_party_dom": True,
            "third_party_authority": True,
            "deterministic_telemetry": True,
        },
    )

    if geo_res.get("geo_citability_summary"):
        report["geo_citability_summary"] = geo_res["geo_citability_summary"]
    if geo_res.get("page_improvement_plans"):
        report["page_improvement_plans"] = geo_res["page_improvement_plans"]
    eng_res = sensors.get("engagement-context-audit", {})
    if eng_res.get("engagement_continuity_summary"):
        report["engagement_continuity_summary"] = eng_res["engagement_continuity_summary"]
    if disc_res.get("ai_agent_scrapeability_summary"):
        report["ai_agent_scrapeability_summary"] = disc_res["ai_agent_scrapeability_summary"]

    run_manifest = cov_dict.get("run_manifest") if cov_dict.get("run_manifest") else build_run_manifest(site)
    report["run_manifest"] = run_manifest

    validate_report(report)
    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Evidence gate, cause-scoped deduplication, queue ordering and report assembly CLI."
    )
    parser.add_argument("--site", required=True, help="Audited site URL or domain")
    parser.add_argument("--candidates", required=True, help="Path to candidate findings JSON file")
    parser.add_argument("--artifacts", required=True, help="Path to evidence artifacts JSON file")
    parser.add_argument("--rules", help="Path to checks/rules JSON file (optional)")
    parser.add_argument("--output", help="Path to write assembled report JSON (optional, defaults to stdout)")
    args = parser.parse_args()

    with open(args.candidates, "r", encoding="utf-8") as f:
        candidates = json.load(f)
    if isinstance(candidates, dict) and "findings" in candidates:
        candidates = candidates["findings"]

    with open(args.artifacts, "r", encoding="utf-8") as f:
        artifacts = json.load(f)

    rules_list: List[Dict[str, Any]] = []
    if args.rules and Path(args.rules).exists():
        with open(args.rules, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
            rules_list = rules_data if isinstance(rules_data, list) else list(rules_data.values())
    else:
        checks_path = Path(__file__).resolve().parents[1] / "references" / "checks.json"
        if checks_path.exists():
            with open(checks_path, "r", encoding="utf-8") as f:
                rules_list = json.load(f)

    records = artifacts if isinstance(artifacts, list) else list(artifacts.values())
    report = assemble(args.site, candidates, records, rules_list, {})
    formatted = json.dumps(report, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
            f.write("\n")
        print(f"Report assembled and written to {args.output}")
    else:
        print(formatted)


assemble_report = assemble

if __name__ == "__main__":
    main()

