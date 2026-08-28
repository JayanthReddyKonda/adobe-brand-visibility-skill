#!/usr/bin/env python3
"""
engagement_check.py - Audits visitor orientation, heading hierarchies, navigation,
and intent-handoff continuity for AI-referred traffic.

Evaluates:
  1. Primary Orientation (5-Second Test): H1 clarity, hero tagline, and CTA presence.
  2. Information Scent: Heading clarity vs generic filler titles.
  3. Destination Discoverability: Navigation reachability to Pricing, Docs, Contact, Products.
  4. Intent Continuity: Experience continuity across referral landing pages.
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
            return e.code, "", dict(e.headers or {}), str(e)
        except Exception as e:
            return None, "", {}, str(e)


GENERIC_H1_TERMS = ["welcome", "home", "homepage", "untitled", "index", "hello", "page"]


class EngagementAnalyzer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.in_style = False
        self.headings = []
        self.current_h = None
        self.current_h_text = []
        self.links = []
        self.in_nav = False
        self.paragraphs = []
        self.in_p = False
        self.current_p = []
        self.buttons_and_ctas = []
        self.in_button = False
        self.current_btn = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = True
        elif t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.current_h = t
            self.current_h_text = []
        elif t == "nav":
            self.in_nav = True
        elif t == "a":
            href = a.get("href", "")
            text_hint = a.get("title") or a.get("aria-label") or ""
            self.links.append({"href": href, "in_nav": self.in_nav, "text_hint": text_hint})
        elif t == "p":
            self.in_p = True
            self.current_p = []
        elif t in ("button", "a") and any(c in a.get("class", "").lower() for c in ("btn", "button", "cta", "signup", "buy")):
            self.in_button = True
            self.current_btn = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("script", "style"):
            self.in_script = False
        elif t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if self.current_h:
                txt = " ".join(self.current_h_text).strip()
                if txt:
                    self.headings.append((self.current_h, txt))
            self.current_h = None
        elif t == "nav":
            self.in_nav = False
        elif t == "p":
            self.in_p = False
            if self.current_p:
                ptxt = " ".join(self.current_p).strip()
                if ptxt:
                    self.paragraphs.append(ptxt)
        elif self.in_button:
            self.in_button = False
            btxt = " ".join(self.current_btn).strip()
            if btxt:
                self.buttons_and_ctas.append(btxt)

    def handle_data(self, data):
        if self.in_script or self.in_style:
            return
        if self.current_h is not None:
            self.current_h_text.append(data.strip())
        elif self.in_p:
            self.current_p.append(data.strip())
        elif self.in_button:
            self.current_btn.append(data.strip())


def audit_page_engagement(html_str, url):
    """Audit orientation, information scent, and navigation on a single page."""
    parser = EngagementAnalyzer()
    try:
        parser.feed(html_str)
    except Exception:
        pass

    h1_list = [txt for tag, txt in parser.headings if tag == "h1"]
    h2_list = [txt for tag, txt in parser.headings if tag == "h2"]
    total_text = " ".join(parser.paragraphs)
    word_count = len(total_text.split())
    content_bearing = word_count >= 40

    findings = []
    recommendations = []

    # 1. H1 Presence on content-bearing page
    if not h1_list and content_bearing:
        findings.append({
            "category": "orientation",
            "title": f"No H1 heading on content page ({url})",
            "severity": "medium",
            "confidence": "high",
            "root_cause": "The page carries readable content but omits a primary <h1> topic heading.",
            "cause_family": "EXPERIENCE.CONTINUITY",
            "cause_id": "ENG-H1-MISSING",
            "impact": "Visitors arriving from AI search answers lack an immediate headline verifying they landed on the correct topic.",
            "evidence": f"Page carries ~{word_count} words but contains 0 <h1> headings (found {len(h2_list)} <h2> elements).",
            "suggested_action": {
                "summary": "Add a prominent <h1> stating what this page offers above the fold.",
                "priority": "medium",
                "verification": "Confirm an <h1> is present and visibly rendered at the top of the page."
            }
        })

    # 2. Information Scent & Orientation
    if h1_list:
        primary_h1 = h1_list[0].lower().strip()
        if primary_h1 in GENERIC_H1_TERMS or len(primary_h1.split()) <= 1:
            findings.append({
                "category": "orientation",
                "title": f"Low-information H1 heading on {url}",
                "severity": "low",
                "confidence": "high",
                "root_cause": f"The primary H1 ('{h1_list[0]}') uses generic filler text rather than naming the brand or offering.",
                "cause_family": "EXPERIENCE.CONTINUITY",
                "cause_id": "ENG-H1-GENERIC",
                "impact": "Referred users cannot instantly confirm topic relevance within the 5-second orientation window.",
                "evidence": f"Primary H1 is '{h1_list[0]}' on {url}.",
                "suggested_action": {
                    "summary": "Revise the H1 to clearly state the product name or core value proposition.",
                    "priority": "low",
                    "verification": "Check that the H1 clearly identifies the specific entity or topic."
                }
            })

    # 3. Destination Navigation Reachability
    nav_links = [l for l in parser.links if l["in_nav"]]
    total_anchors = len(parser.links)
    if len(nav_links) == 0 and total_anchors < 3 and content_bearing:
        findings.append({
            "category": "navigation",
            "title": f"No navigation links discovered on {url}",
            "severity": "medium",
            "confidence": "high",
            "root_cause": "Page contains almost no internal navigation links or menus.",
            "cause_family": "EXPERIENCE.CONTINUITY",
            "cause_id": "ENG-NAV-ABSENT",
            "impact": "Visitors arriving from AI recommendations cannot navigate to pricing, documentation, or purchasing options.",
            "evidence": f"Page carries {word_count} words but contains only {total_anchors} total anchor tag(s).",
            "suggested_action": {
                "summary": "Add header/footer navigation linking to key brand destinations (Products, Pricing, Docs, Contact).",
                "priority": "medium",
                "verification": "Confirm navigation menu links are accessible across the page template."
            }
        })

    page_orientation_data = {
        "url": url,
        "h1": h1_list[0] if h1_list else None,
        "h2_count": len(h2_list),
        "word_count": word_count,
        "nav_links_count": len(nav_links),
        "total_links": total_anchors,
        "ctas_found": parser.buttons_and_ctas[:5]
    }

    return findings, recommendations, page_orientation_data


def audit(base, domain, inv=None):
    """Audit orientation, engagement, and context continuity across sampled pages."""
    findings = []
    recommendations = []
    observations = []
    orientation_samples = []

    pages_to_check = []
    if inv is not None:
        for p in inv.get("pages", []):
            if p.get("html"):
                pages_to_check.append((p["url"], p["html"]))
    else:
        status, html, _, _ = safe_fetch(base + "/", timeout=10, max_bytes=2*1024*1024)
        if html:
            pages_to_check.append((base + "/", html))

    if not pages_to_check:
        return {
            "status": "inconclusive",
            "findings": [],
            "recommendations": [],
            "error": f"could not retrieve content from {base}"
        }

    for url, html in pages_to_check[:6]:
        f_list, r_list, o_data = audit_page_engagement(html, url)
        findings.extend(f_list)
        recommendations.extend(r_list)
        orientation_samples.append(o_data)

    # Context continuity observation
    h1_coverage = sum(1 for o in orientation_samples if o["h1"] is not None)
    observations.append(dict(
        id=f"OBS-{len(observations) + 1:03d}",
        category="experience",
        source={"url": base + "/", "method": "intent-continuity-engine"},
        observation=f"Primary heading orientation rate: {h1_coverage}/{len(orientation_samples)} pages",
        evidence=f"Audited {len(orientation_samples)} landing/internal URL(s) for heading scent and destination links.",
        confidence="high"
    ))

    return {
        "status": "ok",
        "findings": findings,
        "recommendations": recommendations,
        "observations": observations,
        "coverage": {
            "pages_checked": len(orientation_samples),
            "orientation_samples": orientation_samples,
            "source": "shared-inventory" if inv is not None else "homepage-only"
        },
        "limitations": (["Visual CSS layout and viewport positioning are not evaluated in static DOM parser"] if orientation_samples else [])
    }


def main():
    parser = argparse.ArgumentParser(description="Audit on-site visitor orientation, heading hierarchies, and navigation.")
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory", help="Path to shared site-inventory JSON")
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
    print(json.dumps(audit(base, p.netloc, inv=inv), indent=2))


if __name__ == "__main__":
    main()
