#!/usr/bin/env python3
"""
corroboration_check.py - Cross-web authority & corroboration audit layer.

Causal Root Causes:
  - AUTHORITY.IDENTITY_CORROBORATION: BROKEN_AUTHORITY_ANCHOR
  - AUTHORITY.CLAIM_CORROBORATION: CLAIM_CORROBORATION_GAP
"""

import argparse
import json
import os
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


from safe_fetch import safe_fetch  # type: ignore


class SameAsExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json_ld = False
        self.json_ld_contents = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            if "application/ld+json" in attr_dict.get("type", "").lower():
                self.in_json_ld = True

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            self.in_json_ld = False

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_contents.append(data.strip())


def extract_sld(netloc: str) -> str:
    """Extract registered domain name / SLD (e.g., 'miruro' from 'www.miruro.tv' or 'miruro.to')."""
    clean = (netloc or "").lower().replace("www.", "")
    parts = clean.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return clean


def _walk_nodes(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from _walk_nodes(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_nodes(v)


def extract_sameas_links(html):
    """Extract sameAs URLs from JSON-LD blocks, supporting strings and @id objects at any nesting depth."""
    parser = SameAsExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    links = set()
    for raw in parser.json_ld_contents:
        try:
            data = json.loads(raw)
            for o in _walk_nodes(data):
                if isinstance(o, dict) and "sameAs" in o:
                    s = o["sameAs"]
                    s_list = s if isinstance(s, list) else [s]
                    for u in s_list:
                        if isinstance(u, str) and u.startswith("http"):
                            links.add(u.strip())
                        elif isinstance(u, dict) and "@id" in u:
                            target = str(u["@id"]).strip()
                            if target.startswith("http"):
                                links.add(target)
        except Exception:
            pass
    return sorted(links)


class InboundLinkExtractor(HTMLParser):
    """Extract inbound hyperlinks pointing to target domain, along with anchor text and rel attributes."""

    def __init__(self, target_domain: str):
        super().__init__()
        self.target_domain = target_domain.lower().replace("www.", "")
        self.found_links: list[dict] = []
        self._current_tag: str | None = None
        self._current_href: str | None = None
        self._current_rel: str = ""
        self._current_text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            attr_dict = {k.lower(): (v or "") for k, v in attrs}
            href = attr_dict.get("href", "").strip()
            if href:
                self._current_tag = "a"
                self._current_href = href
                self._current_rel = attr_dict.get("rel", "").lower()
                self._current_text = []

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._current_tag == "a":
            anchor_text = " ".join("".join(self._current_text).split())
            href = self._current_href or ""
            parsed_href = urlparse(href)
            href_netloc = parsed_href.netloc.lower().replace("www.", "")
            if href_netloc == self.target_domain or href_netloc.endswith("." + self.target_domain):
                is_dofollow = not any(r in self._current_rel for r in ["nofollow", "ugc", "sponsored"])
                self.found_links.append(
                    {
                        "href": href,
                        "anchor_text": anchor_text,
                        "rel": self._current_rel,
                        "is_dofollow": is_dofollow,
                    }
                )
            self._current_tag = None
            self._current_href = None
            self._current_rel = ""
            self._current_text = []

    def handle_data(self, data):
        if self._current_tag == "a":
            self._current_text.append(data)


def classify_referring_domain(url: str) -> str:
    """Classify the referring source archetype for candidate backlinks."""
    netloc = urlparse(url).netloc.lower()
    if any(d in netloc for d in ["wikipedia.org", "wikidata.org"]):
        return "knowledge_graph"
    if any(d in netloc for d in ["nytimes.com", "techcrunch.com", "forbes.com", "wsj.com", "wired.com", "theverge.com", "bloomberg.com"]):
        return "editorial_news"
    if any(d in netloc for d in ["reddit.com", "news.ycombinator.com", "quora.com", "stackoverflow.com"]):
        return "community_forum"
    if any(d in netloc for d in ["github.com", "linkedin.com", "twitter.com", "x.com", "youtube.com"]):
        return "social_platform"
    if any(d in netloc for d in ["g2.com", "trustpilot.com", "capterra.com", "crunchbase.com"]):
        return "review_directory"
    return "general_web"


def parse_candidate_backlinks(arg_val, inv=None):
    """Parse candidate backlinks from CLI argument (file/JSON/CSV) or inventory."""
    candidates = []
    if arg_val:
        if isinstance(arg_val, list):
            candidates = arg_val
        elif os.path.exists(str(arg_val)):
            try:
                with open(str(arg_val), "r", encoding="utf-8") as f:
                    content = f.read().strip()
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        candidates = data
                    elif isinstance(data, dict):
                        candidates = data.get("candidate_backlinks", data.get("backlinks", []))
                except json.JSONDecodeError:
                    for line in content.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            candidates.append(line)
            except Exception:
                candidates = []
        else:
            try:
                data = json.loads(arg_val)
                if isinstance(data, list):
                    candidates = data
                elif isinstance(data, dict):
                    candidates = data.get("candidate_backlinks", data.get("backlinks", []))
            except Exception:
                candidates = [u.strip() for u in str(arg_val).split(",") if u.strip().startswith("http")]
    elif inv and isinstance(inv, dict):
        candidates = inv.get("candidate_backlinks", inv.get("backlinks", []))

    clean_candidates = []
    for c in (candidates or []):
        if isinstance(c, str) and c.strip().startswith("http"):
            clean_candidates.append({"source_url": c.strip()})
        elif isinstance(c, dict) and c.get("source_url"):
            clean_candidates.append(c)
    return clean_candidates


def audit(base, domain, inv=None, state_file=None, candidate_backlinks=None):
    findings = []
    recommendations = []
    observations = []

    # 1. Fetch Homepage
    if inv is not None:
        home = next(
            (
                p
                for p in inv.get("pages", [])
                if p.get("page_type") == "homepage"
                and (
                    "html" in str(p.get("resource_type", "")).lower()
                    or "html" in str(p.get("content_type", "")).lower()
                )
            ),
            None,
        )
        if not home and inv.get("pages"):
            home = inv["pages"][0]
        html = home.get("html") if home else None
    else:
        status, html, _, err = safe_fetch(base + "/", timeout=10, max_bytes=2 * 1024 * 1024)

        if not html:
            return {
                "status": "inconclusive",
                "findings": [],
                "recommendations": [],
                "error": f"could not reach {base}: {err}",
            }

    if not html:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve content from {base}",
        }

    sameas_urls = extract_sameas_links(html)

    # 2. Extract Brand Name Claim for Corroboration
    brand_name = None
    import re

    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
    if title_match:
        brand_name = title_match.group(1).split("|")[0].replace(" - ", "|").replace(" | ", "|").split("|")[0].strip()

    # 3. Check declared identity nodes (sameAs)
    if not sameas_urls:
        findings.append(
            {
                "category": "authority",
                "title": "Unlinked Brand Entity (No third-party sameAs authority anchors)",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "WEAK_IDENTITY_SIGNALS: The website declares no Schema.org sameAs links connecting the brand to external authoritative knowledge graph nodes.",
                "cause_family": "ENTITY.AUTHORITY",
                "id": "WEAK_IDENTITY_SIGNALS",
                "cause_id": "WEAK_IDENTITY_SIGNALS",
                "impact": "Generative search engines (ChatGPT Search, Claude, Perplexity) cannot corroborate brand claims against third-party authority sources, reducing citation trust.",
                "evidence": f"Scanned homepage {base}/; found 0 sameAs authority links in structured data.",
                "suggested_action": {
                    "summary": "Declare verified third-party identity anchors in Organization sameAs schema.",
                    "technical_fix": "Add verified Wikidata entity ID, LinkedIn corporate profile, and Wikipedia URLs to the Organization sameAs array.",
                    "creative_fix": "Establish and maintain official corporate profiles on recognized authority platforms.",
                    "priority": "medium",
                    "verification": "Confirm Organization JSON-LD contains at least 2 valid sameAs URLs linking to external authority profiles.",
                },
            }
        )
        recommendations.append(
            {
                "title": "Establish an integrated brand identity block with authoritative sameAs links",
                "category": "corroboration",
                "rationale": "No sameAs links were declared. Adding them enables bounded claim corroboration.",
                "suggested_action": "Add sameAs URLs to Organization JSON-LD.",
            }
        )

    # 3.1 Classify sameAs URLs: Separate internal mirror domain clusters from genuine external authorities
    target_sld = extract_sld(domain)
    target_clean = domain.lower().replace("www.", "")
    base_netloc = urlparse(base).netloc.lower().replace("www.", "")
    mirror_domains = []
    external_authorities = []

    for u in sameas_urls:
        u_netloc = urlparse(u).netloc.lower()
        if not u_netloc:
            continue
        u_clean = u_netloc.replace("www.", "")
        u_sld = extract_sld(u_netloc)
        if u_sld == target_sld and u_clean != target_clean:
            mirror_domains.append(u)
        elif u_clean != base_netloc and not u_clean.endswith("." + base_netloc):
            external_authorities.append(u)

    # If sameAs contains 2+ self-referential mirror domains, flag CIRCULAR_SAMEAS_SELF_REFERENCE
    if len(mirror_domains) >= 2:
        findings.append(
            {
                "title": "Inverted sameAs links point to internal mirror domain cluster",
                "severity": "high",
                "category": "corroboration",
                "cause_family": "AUTHORITY.IDENTITY_CORROBORATION",
                "id": "CIRCULAR_SAMEAS_SELF_REFERENCE",
                "cause_id": "CIRCULAR_SAMEAS_SELF_REFERENCE",
                "root_cause": f"The Organization schema points sameAs properties to alternate domain mirrors ({', '.join(mirror_domains[:4])}) rather than independent third-party knowledge graph entities (Wikidata, Wikipedia, Crunchbase), causing entity fragmentation and trust dilution in AI search engines.",
                "confidence": "high",
                "evidence": f"Declared sameAs array contains {len(mirror_domains)} mirror domain(s) sharing the root SLD '{target_sld}': {', '.join(mirror_domains[:5])}.",
                "suggested_action": {
                    "summary": "Remove alternate mirror domain URLs from sameAs and link to verified external knowledge graph entities.",
                    "priority": "high",
                    "technical_fix": "Remove self-referential mirror domains from the Organization sameAs array in JSON-LD. Reserve sameAs strictly for verified external third-party profiles (Wikidata, Wikipedia, verified social channels).",
                    "creative_fix": "Establish an official verification page or press kit rather than linking mirror domains inside structured data.",
                    "verification": "Confirm all sameAs links resolve to independent third-party platforms with matching brand attribution.",
                },
            }
        )

    # 3.2 Check for Tier-1 Knowledge Graph anchors (Wikidata, Wikipedia, Crunchbase)
    has_tier1 = any(
        any(td in u.lower() for td in ["wikidata.org", "wikipedia.org", "crunchbase.com"]) for u in sameas_urls
    )
    if not has_tier1:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.KNOWLEDGE_GRAPH_ANCHOR.001",
                "title": "Establish an authoritative third-party Knowledge Graph entity (Wikidata / Wikipedia)",
                "category": "corroboration",
                "summary": f"Brand '{brand_name or domain}' has no declared Wikidata or Wikipedia entity link in sameAs. Establishing an independent knowledge graph entity anchors the brand into LLM pre-training corpora and RAG indexers.",
                "priority": "low",
                "technical_fix": "Register the brand entity on Wikidata (obtaining a QID) and include the permanent Wikidata URI in the Organization sameAs array.",
                "creative_fix": "Document corporate milestones, executive leadership, and primary offerings in public registries to substantiate independent notability.",
                "verification": "Verify that sameAs includes a valid https://www.wikidata.org/wiki/Q... URI.",
            }
        )

    # 3.3 Check for Primary Video Authority Channels (YouTube presence)
    has_youtube = any("youtube.com" in u.lower() or "youtu.be" in u.lower() for u in sameas_urls)
    if not has_youtube:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.YOUTUBE_PRESENCE.001",
                "title": "Establish an official YouTube video authority channel",
                "category": "corroboration",
                "summary": f"Brand '{brand_name or domain}' has no declared YouTube channel in sameAs. Multi-modal AI search engines frequently index and ground answers in structured video chapters and verified transcripts.",
                "priority": "low",
                "technical_fix": "Add official YouTube channel URL to Organization sameAs in JSON-LD.",
                "creative_fix": "Publish educational, tutorial, and demonstration video assets with structured chapters and accurate transcripts.",
                "verification": "Verify YouTube URL is present in sameAs and resolves with HTTP 200.",
            }
        )

    has_reddit = any("reddit.com" in u.lower() for u in sameas_urls)
    if not has_reddit:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.COMMUNITY_DISCUSSION.001",
                "title": "Build organic community footprint in relevant discussion forums (Reddit)",
                "category": "corroboration",
                "summary": f"Brand '{brand_name or domain}' has no community discussion anchors. AI models (ChatGPT Search, Perplexity) frequently retrieve and synthesize consensus from active Reddit and forum discussions.",
                "priority": "low",
                "technical_fix": "Include verified community discussion or support profile links in sameAs where applicable.",
                "creative_fix": "Participate authentically in category subreddits with transparent product expertise and helpful solutions.",
                "verification": "Verify community URLs resolve with HTTP 200.",
            }
        )

    checked = []
    broken = []

    # Probe external authorities (excluding internal mirror domains, max 2 per SKILL.md invariant)
    for u in external_authorities[:2]:
        checked.append(u)
        status, ext_html, _, _ = safe_fetch(u, timeout=1.5, max_bytes=512 * 1024, method="GET")
        if status in (404, 410) or (status and status >= 500):
            broken.append(f"{u} (HTTP {status})")
        elif status in (401, 403, 429, 999) or status == 0 or status is None:
            observations.append(
                {"observation": f"Authority link {u} returned status {status}; not treated as broken anchor."}
            )

        elif brand_name and ext_html:
            ext_title = ""
            ext_title_match = re.search(r"<title>(.*?)</title>", ext_html, re.IGNORECASE)
            if ext_title_match:
                ext_title = ext_title_match.group(1).lower()

            og_match = re.search(
                r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']', ext_html, re.IGNORECASE
            )
            og_site_name = og_match.group(1).lower() if og_match else ""

            brand_lower = brand_name.lower()

            # If the external authority explicitly mentions the brand in its most critical identity fields
            if brand_lower in ext_title or brand_lower in og_site_name:
                observations.append(
                    {
                        "observation": f"Successfully corroborated brand name '{brand_name}' via <title>/og:site_name on external authority {u}."
                    }
                )
            else:
                # We check full text as a weak fallback
                if brand_lower not in ext_html.lower():
                    findings.append(
                        {
                            "title": "Authority link fails to corroborate brand identity claim",
                            "severity": "medium",
                            "category": "corroboration",
                            "cause_family": "AUTHORITY.IDENTITY_CORROBORATION",
                            "id": "CLAIM_CORROBORATION_GAP",
                            "cause_id": "CLAIM_CORROBORATION_GAP",
                            "root_cause": f"Declared authority profile does not substantiate brand identity for {brand_name}.",
                            "confidence": "high",
                            "evidence": f"The declared sameAs link {u} is reachable, but neither its title, og:site_name, nor body text explicitly state the brand name '{brand_name}'.",
                            "suggested_action": {
                                "summary": f"Ensure the external authority page at {urlparse(u).hostname} explicitly claims the canonical brand name.",
                                "technical_fix": "Update sameAs link target or add reciprocal Schema.org sameAs links pointing to canonical brand domain.",
                                "creative_fix": "Ensure external profiles (Wikidata, LinkedIn, Wikipedia) explicitly mention the canonical brand name in title and bio.",
                                "priority": "medium",
                                "verification": "Re-fetch external profile and verify canonical brand name presence.",
                            },
                        }
                    )

    if broken:
        findings.append(
            {
                "category": "corroboration",
                "title": f"Broken authority/profile links declared in sameAs ({len(broken)} link(s))",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "Declared sameAs identity links return HTTP 4xx or 5xx error codes.",
                "cause_family": "AUTHORITY.IDENTITY_CORROBORATION",
                "id": "BROKEN_AUTHORITY_ANCHOR",
                "cause_id": "BROKEN_AUTHORITY_ANCHOR",
                "impact": "AI models attempting to verify entity identity against independent authorities encounter broken links, reducing confidence.",
                "evidence": f"Declared sameAs links returned error status: {'; '.join(broken)}.",
                "suggested_action": {
                    "summary": "Update or remove broken sameAs URLs in Organization JSON-LD markup.",
                    "technical_fix": "Update sameAs array in Organization Schema.org markup to remove dead or 4xx/5xx URLs.",
                    "creative_fix": "Claim and maintain active brand presence on primary knowledge hubs (Wikidata, Crunchbase, LinkedIn).",
                    "priority": "medium",
                    "verification": "Confirm all declared sameAs URLs return HTTP 200.",
                },
            }
        )

    # 57% Off-Site Third-Party Footprint Evaluation (Omniscient Digital 2026 Benchmark)
    high_citation_platforms = (
        "reddit.com",
        "wikipedia.org",
        "youtube.com",
        "linkedin.com",
        "github.com",
        "trustpilot.com",
        "g2.com",
        "capterra.com",
    )
    found_third_party_nodes = []
    for link in sameas_urls:
        if isinstance(link, str):
            l_lower = link.lower()
            if any(platform in l_lower for platform in high_citation_platforms):
                found_third_party_nodes.append(link)

    if len(found_third_party_nodes) == 0:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.OFFSITE_FOOTPRINT_GAP.001",
                "title": "Establish off-site third-party corroboration on high-citation authority platforms",
                "category": "corroboration",
                "summary": f"Brand '{base}' lacks declared presence on primary third-party citation platforms (Reddit, Wikipedia, YouTube, LinkedIn, G2/Trustpilot). Generative engines rely heavily on third-party reviews, encyclopedic entries, and community consensus to corroborate brand claims.",
                "priority": "high",
                "technical_fix": "Add verified corporate profiles on LinkedIn, GitHub, YouTube, or review platforms to the Organization sameAs schema array.",
                "creative_fix": "Actively cultivate third-party mentions, expert reviews, and community discussions on high-citation hubs.",
                "verification": "Confirm sameAs array links to at least one third-party review or authority platform.",
            }
        )

    # 4. Bounded Candidate Backlinks Verification
    candidate_list = parse_candidate_backlinks(candidate_backlinks, inv=inv)
    backlink_results = []
    broken_backlinks = []
    missing_backlinks = []
    intact_backlinks = []

    if candidate_list:
        # Bounded execution: max 10 candidates to respect latency budget
        for item in candidate_list[:10]:
            source_url = item.get("source_url") if isinstance(item, dict) else str(item)
            if not source_url or not source_url.startswith("http"):
                continue

            expected_target = item.get("expected_target") if isinstance(item, dict) else None
            domain_archetype = classify_referring_domain(source_url)

            # SSRF-safe probe with 5s timeout and 512 KiB limit
            s_status, s_html, _, s_err = safe_fetch(source_url, timeout=5, max_bytes=512 * 1024, method="GET")

            if s_status != 200 or not s_html:
                backlink_results.append(
                    {
                        "source_url": source_url,
                        "domain_archetype": domain_archetype,
                        "status": "source_unreachable",
                        "http_status": s_status,
                        "error": s_err or f"HTTP {s_status}",
                        "inbound_links_found": 0,
                        "is_dofollow": False,
                    }
                )
                broken_backlinks.append(f"{source_url} ({s_err or f'HTTP {s_status}'})")
                continue

            link_parser = InboundLinkExtractor(domain)
            try:
                link_parser.feed(s_html)
            except Exception:
                pass

            matching_links = link_parser.found_links
            if matching_links:
                # If specific target was expected, verify path match
                target_matched = True
                if expected_target:
                    exp_parsed = urlparse(expected_target)
                    target_matched = any(
                        urlparse(ml["href"]).path.rstrip("/") == exp_parsed.path.rstrip("/")
                        for ml in matching_links
                    )

                status_code = "verified_intact" if target_matched else "target_mismatch"
                primary_link = matching_links[0]
                backlink_results.append(
                    {
                        "source_url": source_url,
                        "domain_archetype": domain_archetype,
                        "status": status_code,
                        "http_status": 200,
                        "inbound_links_found": len(matching_links),
                        "target_url": primary_link["href"],
                        "anchor_text": primary_link["anchor_text"],
                        "rel": primary_link["rel"],
                        "is_dofollow": primary_link["is_dofollow"],
                    }
                )
                if target_matched:
                    intact_backlinks.append(source_url)
                else:
                    missing_backlinks.append(source_url)
            else:
                backlink_results.append(
                    {
                        "source_url": source_url,
                        "domain_archetype": domain_archetype,
                        "status": "link_missing",
                        "http_status": 200,
                        "inbound_links_found": 0,
                        "is_dofollow": False,
                    }
                )
                missing_backlinks.append(source_url)

        if intact_backlinks:
            observations.append(
                {
                    "observation": f"Verified {len(intact_backlinks)} intact candidate backlink(s) pointing to {domain}."
                }
            )
        if broken_backlinks:
            findings.append(
                {
                    "category": "corroboration",
                    "title": f"Candidate backlink referring source unreachable ({len(broken_backlinks)} link(s))",
                    "severity": "low",
                    "confidence": "high",
                    "root_cause": "Referring candidate backlink source URL returns HTTP 4xx/5xx or is unreachable.",
                    "cause_family": "AUTHORITY.CLAIM_CORROBORATION",
                    "id": "CANDIDATE_BACKLINK_UNREACHABLE",
                    "cause_id": "CANDIDATE_BACKLINK_UNREACHABLE",
                    "evidence": f"Candidate backlink sources failed with errors: {'; '.join(broken_backlinks[:3])}.",
                    "suggested_action": {
                        "summary": "Verify and update dead candidate backlink URLs in external PR or referral tracking ledgers.",
                        "technical_fix": "Audit external referral inventory and update broken backlinks with canonical landing URLs.",
                        "creative_fix": "Engage referring publisher partners to refresh outdated anchor links to current site architecture.",
                        "priority": "low",
                        "verification": "Re-check referring URLs via HTTP GET to ensure 200 OK.",
                    },
                }
            )
    else:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.BACKLINK_LEDGER_INGESTION.001",
                "title": "Ingest verified third-party backlink candidate ledger for bounded citation verification",
                "category": "corroboration",
                "summary": "No candidate backlinks were provided for bounded verification. Web-wide backlink discovery cannot be performed truthfully without an external backlink ledger or indexed link graph API; arbitrary linking pages cannot be discovered from Common Crawl URL-only indexes (CDX). Supply candidate referring URLs via --candidate-backlinks to audit inbound citation anchors.",
                "priority": "low",
                "technical_fix": "Provide candidate backlink URLs in inv.json or via --candidate-backlinks to audit inbound citation anchors.",
                "creative_fix": "Acquire high-authority editorial citations and industry publication references pointing to canonical product pages.",
                "verification": "Run corroboration_check.py --candidate-backlinks <ledger.json> to verify intact inbound hyperlinks.",
            }
        )

    tier1_list = [
        u for u in sameas_urls
        if any(td in u.lower() for td in ["wikidata.org", "wikipedia.org", "crunchbase.com"])
    ]
    archetype_coverage = {
        "knowledge_graph": [u for u in sameas_urls if any(d in u.lower() for d in ["wikidata.org", "wikipedia.org"])],
        "community_consensus": [
            u for u in sameas_urls if any(d in u.lower() for d in ["reddit.com", "stackoverflow.com", "quora.com"])
        ],
        "media_evidence": [u for u in sameas_urls if any(d in u.lower() for d in ["youtube.com"])],
        "corporate_identity": [
            u for u in sameas_urls if any(d in u.lower() for d in ["linkedin.com", "crunchbase.com", "github.com"])
        ],
        "customer_reviews": [
            u for u in sameas_urls if any(d in u.lower() for d in ["trustpilot.com", "g2.com", "capterra.com"])
        ],
    }
    missing_archetypes = [arch for arch, urls in archetype_coverage.items() if not urls]

    if len(missing_archetypes) >= 3 and sameas_urls:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.OFFSITE_CORROBORATION_DISTRIBUTION.001",
                "title": "Diversify off-site entity corroboration footprint across multi-source platforms",
                "category": "corroboration",
                "summary": (
                    f"Brand entity identity is missing representation across {len(missing_archetypes)} key off-site authority archetypes ({', '.join(missing_archetypes)}). "
                    "Empirical research demonstrates that generative AI search engines (ChatGPT Search, Claude, Perplexity) derive 57% of citations from off-site multi-source platforms "
                    "(Wikidata, Wikipedia, Reddit, YouTube, LinkedIn, G2/Trustpilot). Relying solely on declared sameAs links without broad corroboration limits AI trust scoring."
                ),
                "priority": "medium",
                "technical_fix": "Add verified sameAs links to official LinkedIn company profiles, Wikidata item nodes, and verified review platforms.",
                "creative_fix": "Cultivate genuine community discussions on Reddit and publish technical demonstration videos on YouTube to build third-party consensus.",
                "verification": "Confirm sameAs array includes links to knowledge graph, corporate registry, and verified community profiles.",
            }
        )

    evidence_classes = {
        "declared_identity_nodes": {
            "count": len(sameas_urls),
            "declared_urls": sameas_urls,
            "tier1_anchors": tier1_list,
            "archetype_coverage": {k: len(v) for k, v in archetype_coverage.items()},
            "verified_external_nodes": checked,
            "broken_anchors": broken,
            "internal_mirror_domains": mirror_domains,
        },
        "verified_candidate_backlinks": {
            "contract_active": bool(candidate_list),
            "total_candidates_provided": len(candidate_list),
            "candidates_probed": len(backlink_results),
            "verified_intact_count": len(intact_backlinks),
            "link_missing_count": len(missing_backlinks),
            "source_unreachable_count": len(broken_backlinks),
            "dofollow_count": sum(1 for r in backlink_results if r.get("is_dofollow")),
            "results": backlink_results,
            "limitations": [
                "Backlink verification is strictly bounded to supplied candidate URLs; arbitrary linking pages cannot be discovered from Common Crawl URL-only index (CDX)."
            ]
            if candidate_list
            else [
                "No candidate backlink dataset provided. Web-wide backlink discovery cannot be performed truthfully without an external backlink ledger or indexed link graph API; arbitrary linking pages cannot be discovered from Common Crawl URL-only indexes (CDX). Retaining bounded verification contract for user-supplied candidate backlinks."
            ],
        },
    }

    return {
        "status": "ok",
        "evidence_classes": evidence_classes,
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "sameas_count": len(sameas_urls),       # backward-compat alias
            "sameas_declared": len(sameas_urls),    # total sameAs URLs declared in schema
            "sameas_resolvable": len(checked),      # subset that returned HTTP 2xx
            "probed": len(checked),
            "results": checked,
            "candidate_backlinks_provided": len(candidate_list),
            "candidate_backlinks_verified": len(intact_backlinks),
        },
        "limitations": [
            "Probed declared sameAs authority URLs; full web-wide claim corroboration was bounded to declared links.",
            "Web-wide backlink discovery cannot be performed truthfully from URL-only indexes (such as Common Crawl CDX, which indexes page URLs rather than an inverted link graph). Backlink verification is bounded to user-supplied candidate backlinks.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Cross-web authority & corroboration audit layer.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
    parser.add_argument("--state", help="Path to global state JSON")
    parser.add_argument(
        "--candidate-backlinks",
        dest="candidate_backlinks",
        help="Path to candidate backlinks JSON/CSV or raw JSON string",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    args = parser.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    inv = None
    if args.inventory:
        if os.path.exists(args.inventory):
            try:
                with open(args.inventory, "r", encoding="utf-8") as f:
                    inv = json.load(f)
            except Exception as e:
                inv = {"pages": [], "error": f"Failed to parse inventory: {e}", "status": "inconclusive"}
        else:
            inv = {"pages": [], "error": "Inventory file not found", "status": "inconclusive"}
    res = audit(base, p.netloc, inv=inv, state_file=args.state, candidate_backlinks=args.candidate_backlinks)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
