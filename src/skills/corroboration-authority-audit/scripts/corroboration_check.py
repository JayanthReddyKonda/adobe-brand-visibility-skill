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


from safe_fetch import safe_fetch


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


def extract_sameas_links(html):
    """Extract sameAs URLs from JSON-LD blocks, supporting strings and @id objects."""
    parser = SameAsExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    links = set()
    for raw in parser.json_ld_contents:
        try:
            data = json.loads(raw)
            objs = data if isinstance(data, list) else [data]
            if isinstance(data, dict) and "@graph" in data:
                objs = data["@graph"]
            for o in objs:
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


def audit(base, domain, inv=None, state_file=None):
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

    # 3. Check declared authority links and perform Bounded Claim Corroboration
    if not sameas_urls:
        recommendations.append(
            {
                "title": "Establish an integrated brand identity block with authoritative sameAs links",
                "category": "corroboration",
                "rationale": "No sameAs links were declared. Adding them enables bounded claim corroboration.",
                "suggested_action": "Add sameAs URLs to Organization JSON-LD.",
            }
        )
        return {"status": "ok", "findings": findings, "recommendations": recommendations, "observations": observations}

    # 3.1 Classify sameAs URLs: Separate internal mirror domain clusters from genuine external authorities
    target_sld = extract_sld(domain)
    target_clean = domain.lower().replace("www.", "")
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
        elif not u.startswith(base):
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

    # 3.3 Check for High-Correlation AI Citation Channels (YouTube: 0.737 correlation, Reddit)
    has_youtube = any("youtube.com" in u.lower() or "youtu.be" in u.lower() for u in sameas_urls)
    if not has_youtube:
        recommendations.append(
            {
                "id": "PROACTIVE.AUTHORITY.YOUTUBE_PRESENCE.001",
                "title": "Establish an official YouTube video authority channel",
                "category": "corroboration",
                "summary": f"Brand '{brand_name or domain}' has no declared YouTube channel in sameAs. Empirical studies reveal YouTube brand mentions correlate most strongly (~0.737) with generative AI citations, outperforming backlinks 3:1.",
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

    # Probe external authorities (excluding internal mirror domains)
    for u in external_authorities[:5]:
        checked.append(u)
        status, ext_html, _, _ = safe_fetch(u, timeout=5, max_bytes=512 * 1024, method="GET")
        if status != 200:
            broken.append(f"{u} (HTTP {status})")

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
                                "priority": "medium",
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
                "summary": f"Brand '{base}' lacks declared presence on the top third-party citation platforms (Reddit, Wikipedia, YouTube, LinkedIn, G2/Trustpilot). Empirical research across 23,387 branded AI search citations demonstrates that 57% of citations derive from third-party reviews and listicles, while only ~4.5% originate from a brand's own pages.",
                "priority": "high",
                "technical_fix": "Add verified corporate profiles on LinkedIn, GitHub, YouTube, or review platforms to the Organization sameAs schema array.",
                "creative_fix": "Actively cultivate third-party mentions, expert reviews, and community discussions on high-citation hubs.",
                "verification": "Confirm sameAs array links to at least one third-party review or authority platform.",
            }
        )

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {"sameas_count": len(sameas_urls), "probed": len(checked), "results": checked},
        "limitations": [
            "Probed declared sameAs authority URLs; full web-wide claim corroboration was bounded to declared links."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Cross-web authority & corroboration audit layer.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
    parser.add_argument("--state", help="Path to global state JSON")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format (default: json)")
    args = parser.parse_args()
    s = args.site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urlparse(s)
    base = f"{p.scheme}://{p.netloc}"
    inv = None
    if args.inventory and os.path.exists(args.inventory):
        try:
            with open(args.inventory, "r", encoding="utf-8") as f:
                inv = json.load(f)
        except Exception:
            inv = None
    res = audit(base, p.netloc, inv=inv, state_file=args.state)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
