#!/usr/bin/env python3
"""
engagement_check.py - Engagement & context continuity layer.

Causal Root Causes:
  - EXPERIENCE.CONTINUITY: INTENT_TO_LANDING_MISMATCH, LOW_INFORMATION_SCENT, DESTINATION_NAVIGATION_FRICTION

Evaluates the complete Intent -> Expected Facts -> Landing Page -> Information Scent -> Next Action journey.
Enforces strict Resource Invariant: Only genuine HTML pages enter engagement audits.
"""
import sys
import os
import re
import json
import argparse
from html.parser import HTMLParser
from urllib.parse import urlparse

try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "audit-orchestrator", "scripts")))
    from safe_fetch import safe_fetch, safe_check_status, DEFAULT_USER_AGENT
except ImportError:
    import urllib.request, urllib.error
    DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; BrandReadinessBot/1.0; +https://agentskills.io)"
    def safe_fetch(url, timeout=10, max_bytes=2*1024*1024, user_agent=DEFAULT_USER_AGENT, method="GET"):
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(max_bytes).decode("utf-8", "ignore"), dict(r.headers), None
        except urllib.error.HTTPError as e:
            try:
                body = e.read(max_bytes).decode("utf-8", "ignore")
            except Exception:
                body = ""
            return e.code, body, dict(e.headers or {}), str(e)
        except Exception as e:
            return None, "", {}, str(e)

GENERIC_H1_TERMS = {
    "welcome", "home", "homepage", "untitled", "index", "hello",
    "welcome to our website", "welcome to our site", "main page", "overview"
}

CORE_DESTINATIONS = ["pricing", "product", "docs", "documentation", "about", "contact", "login", "signup", "shop", "store"]


class EngagementDOMParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.title = ""
        self.in_title = False
        self.h1_list = []
        self.h2_list = []
        self.current_tag = None
        self.current_text = []
        self.body_text = []
        self.nav_links = []
        self.ctas = []

    def handle_starttag(self, tag, attrs):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower in ("script", "style", "noscript"):
            self.in_script = True
        elif tag_lower == "title":
            self.in_title = True
        elif tag_lower in ("h1", "h2"):
            self.current_tag = tag_lower
            self.current_text = []
        elif tag_lower == "a":
            href = attr_dict.get("href", "")
            if href:
                self.nav_links.append(href)
                cls = attr_dict.get("class", "").lower()
                role = attr_dict.get("role", "").lower()
                if "btn" in cls or "button" in cls or "cta" in cls or role == "button":
                    self.ctas.append(href)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in ("script", "style", "noscript"):
            self.in_script = False
        elif tag_lower == "title":
            self.in_title = False
        elif tag_lower == "h1":
            if self.current_text:
                self.h1_list.append(" ".join(self.current_text).strip())
            self.current_tag = None
        elif tag_lower == "h2":
            if self.current_text:
                self.h2_list.append(" ".join(self.current_text).strip())
            self.current_tag = None

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        elif self.current_tag in ("h1", "h2"):
            self.current_text.append(data.strip())
        elif not self.in_script:
            txt = data.strip()
            if txt:
                self.body_text.append(txt)


def audit_page_engagement(html_content, url, page_type="other"):
    """Evaluate 5-second orientation, information scent, and intent continuity across multiple signals."""
    findings = []
    recommendations = []
    observations = []

    dom = EngagementDOMParser()
    try:
        dom.feed(html_content)
    except Exception:
        pass

    full_text = " ".join(dom.body_text)
    visible_words = len(full_text.split())
    has_descriptive_title = len(dom.title.strip().split()) >= 3
    has_subheadings = len(dom.h2_list) >= 1

    # 1. Multi-Signal 5-Second Orientation & Information Scent
    if not dom.h1_list:
        if not has_descriptive_title and not has_subheadings and visible_words > 80:
            findings.append({
                "category": "engagement",
                "title": f"Weak first-visit orientation and missing primary topic statement ({url})",
                "severity": "medium",
                "confidence": "high",
                "root_cause": "The page lacks both an <h1> heading and descriptive title/subheading markers, leaving arriving visitors unoriented.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "cause_id": "LOW_INFORMATION_SCENT",
                "impact": "Visitors arriving from AI search answers cannot quickly verify the page purpose, increasing bounce probability.",
                "evidence": f"Found 0 <h1> tags, 0 <h2> tags, and an uninformative <title> ('{dom.title}') on {url}.",
                "suggested_action": {
                    "summary": "Add a descriptive <h1> headline above the fold clearly stating the offering name and value proposition.",
                    "priority": "medium",
                    "verification": f"Confirm {url} contains an <h1> stating the core offering topic."
                }
            })
        elif visible_words > 80:
            recommendations.append({
                "title": f"Add semantic <h1> element on {url}",
                "category": "engagement",
                "rationale": f"Page provides context in <title> ('{dom.title}') but lacks an explicit <h1> heading for semantic structure.",
                "suggested_action": "Add an <h1> heading matching the page title to strengthen heading information scent."
            })
    else:
        primary_h1 = dom.h1_list[0].strip()
        h1_clean = primary_h1.lower()
        if h1_clean in GENERIC_H1_TERMS or len(primary_h1.split()) <= 1:
            findings.append({
                "category": "engagement",
                "title": f"Low-information generic headline on landing page ('{primary_h1}')",
                "severity": "low",
                "confidence": "high",
                "root_cause": f"The primary headline ('{primary_h1}') is generic and conveys weak information scent.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "cause_id": "LOW_INFORMATION_SCENT",
                "impact": "Visitors skimming above-the-fold content cannot determine the brand's core offering within 5 seconds.",
                "evidence": f"Primary <h1> on {url} is '{primary_h1}'.",
                "suggested_action": {
                    "summary": "Revise the <h1> to include concrete product nouns and value verbs (e.g. 'Artisanal Fresh Roasted Specialty Coffee').",
                    "priority": "low",
                    "verification": "Confirm updated H1 contains descriptive brand or product terminology."
                }
            })

    # 2. Destination Discoverability & Navigation Friction
    nav_links_text = " ".join(dom.nav_links).lower()
    found_destinations = [d for d in CORE_DESTINATIONS if d in nav_links_text]

    if not found_destinations and len(dom.nav_links) < 3 and visible_words > 100:
        findings.append({
            "category": "engagement",
            "title": f"Restricted destination navigation on landing page ({url})",
            "severity": "medium",
            "confidence": "medium",
            "root_cause": "The page lacks navigation links to core brand destinations (Pricing, Docs, Products, Contact).",
            "cause_family": "EXPERIENCE.CONTINUITY",
            "cause_id": "DESTINATION_NAVIGATION_FRICTION",
            "impact": "Visitors referred from specific AI answers cannot navigate deeper into related brand resources, causing journey abandonment.",
            "evidence": f"Found {len(dom.nav_links)} navigation links on {url}; missing links to core sections ({', '.join(CORE_DESTINATIONS[:4])}).",
            "suggested_action": {
                "summary": "Add header/footer navigation links to key brand destinations (Pricing, Products, Documentation, Contact).",
                "priority": "medium",
                "verification": f"Verify {url} contains discoverable links to core destinations."
            }
        })

    # 3. Intent-to-Landing Match for Specialized Pages
    if page_type == "pricing" and not any(k in full_text.lower() for k in ("$", "₹", "usd", "inr", "eur", "£", "free", "tier", "plan", "/mo")):
        findings.append({
            "category": "intent-continuity",
            "title": f"Intent-to-landing mismatch: Pricing page omits transparent commercial terms ({url})",
            "severity": "medium",
            "confidence": "high",
            "root_cause": "A pricing-designated landing route contains no visible price figures, plan tiers, or indicative pricing ranges.",
            "cause_family": "EXPERIENCE.CONTINUITY",
            "cause_id": "INTENT_TO_LANDING_MISMATCH",
            "impact": "Visitors referred by pricing comparison queries encounter a content gap, immediately bouncing.",
            "evidence": f"Pricing page ({url}) contains 0 numerical price figures or plan tier indicators.",
            "suggested_action": {
                "summary": "Publish transparent tier pricing or starting ranges above the fold on the pricing landing page.",
                "priority": "medium",
                "verification": f"Confirm {url} displays clear pricing tiers and commercial terms."
            }
        })

    return findings, recommendations, {
        "url": url,
        "h1": dom.h1_list,
        "h2_count": len(dom.h2_list),
        "visible_words": visible_words,
        "navigation_links_found": len(dom.nav_links),
        "core_destinations_found": found_destinations
    }


def audit(base, domain, inv=None):
    findings = []
    recommendations = []
    observations = []
    page_metrics = []

    html_pages = []
    if inv is not None:
        for p in inv.get("pages", []):
            u = p.get("url", "")
            raw_html = p.get("html", "")
            if u.lower().endswith((".xml", ".xml.gz", ".txt", ".json", ".pdf")):
                continue
            if raw_html.strip().startswith("<?xml") or "<urlset" in raw_html.lower() or "<sitemapindex" in raw_html.lower():
                continue
            if raw_html:
                html_pages.append(p)
    else:
        status, html, _, _ = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if html:
            html_pages.append({"url": base + "/", "html": html, "page_type": "homepage"})

    for p in html_pages:
        p_findings, p_recs, p_data = audit_page_engagement(p["html"], p["url"], page_type=p.get("page_type", "other"))
        findings.extend(p_findings)
        recommendations.extend(p_recs)
        page_metrics.append(p_data)

    if not page_metrics:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve HTML content from {base}"
        }

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "html_pages_evaluated": len(page_metrics),
            "page_details": page_metrics
        },
        "limitations": [
            "Evaluated structural heading hierarchy, above-the-fold information scent, and navigation destination reachability from raw HTML."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Audit on-site visitor orientation, heading hierarchies, and navigation.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
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
    res = audit(base, p.netloc, inv=inv)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
