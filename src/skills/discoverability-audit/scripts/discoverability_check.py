import argparse
import urllib.parse
import re
from http import safe_fetch, safe_check_status
from telemetry import TelemetryResponse, TelemetryFact
from dom import UnifiedDOMParser

AI_BOTS = ["GPTBot", "ChatGPT-User", "ClaudeBot", "Claude-Web", "PerplexityBot", "Google-Extended"]

def parse_domain(site):
    s = site.strip()
    if not s.startswith("http"):
        s = "https://" + s
    p = urllib.parse.urlparse(s)
    return f"{p.scheme}://{p.netloc}", p.netloc

def audit(base_url, domain, inv=None, state_file=None):
    html = ""
    status = 200
    if inv and inv.get("pages"):
        home = next((p for p in inv["pages"] if p.get("page_type") == "homepage"), inv["pages"][0])
        html = home.get("html", "")
        status = home.get("status", 200)
    else:
        status, html, _, _ = safe_fetch(base_url + "/")
    
    if not html:
        return TelemetryResponse(status="inconclusive", telemetry={}, raw_extracted_facts=[], error="No HTML")

    dom = UnifiedDOMParser()
    dom.feed(html)
    visible_words = dom.get_visible_words_count()
    
    r_txt = ""
    r_status = 200
    if inv and "robots_txt" in inv:
        r_txt = inv["robots_txt"]
    else:
        r_status, r_txt, _, _ = safe_fetch(base_url + "/robots.txt")

    facts = []
    telemetry = {
        "visible_words_initial_html": visible_words,
        "robots_txt_status": r_status,
        "canonical_declared": dom.canonical,
        "meta_robots_declared": dom.meta_robots
    }

    if visible_words < 25:
        facts.append(TelemetryFact(
            fact_type="rendering_issue",
            evidence=f"Initial HTML contains only {visible_words} visible words, indicating a JS-rendered shell.",
            metadata={"visible_words": visible_words}
        ))
        
    if r_status == 200 and r_txt:
        # Simplistic regex for testing
        blocked_bots = []
        for bot in AI_BOTS:
            if re.search(rf'User-agent:\s*{bot}.*?Disallow:\s*/', r_txt, re.IGNORECASE | re.DOTALL):
                blocked_bots.append(bot)
        if blocked_bots:
            facts.append(TelemetryFact(
                fact_type="robots_txt_block",
                evidence=f"robots.txt disallows AI search crawlers: {', '.join(blocked_bots)}",
                metadata={"blocked_crawlers": blocked_bots}
            ))

    return TelemetryResponse(status="ok", telemetry=telemetry, raw_extracted_facts=facts)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", required=True)
    parser.add_argument("--inventory")
    parser.add_argument("--format", default="json")
    args = parser.parse_args()
    base, domain = parse_domain(args.site)
    res = audit(base, domain)
    print(res.to_json())

