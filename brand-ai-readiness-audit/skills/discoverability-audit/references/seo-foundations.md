# SEO Foundations (discoverability reference)

A compact internal reference for the deterministic checks the discoverability
skill performs against a site's public infrastructure. It is deliberately scoped
to what can be measured from raw HTTP/HTML without a browser, and it avoids
turning generic SEO folklore into automated defects.

## What is really being checked

The core question is not "does this page use good SEO?" but:

> **Is the important content present and reachable for the relevant retrieval
> client?**

That is why JavaScript-rendering is NOT itself a defect: Google renders with
Chromium and supports JS. The only render-adjacent risk we assert is when the
initial HTML response carries almost no visible text (a *risk* for clients that
do not execute JS — stated as a risk, never as a proven outage).

## robots.txt

- Parsed per RFC 9309-style groups: `User-agent:` groups with their `Allow` /
  `Disallow` / `Sitemap` lines; longest-match path rules with `*`/`$` wildcards.
- **Disallow ≠ index control.** robots.txt only controls crawling; `noindex`
  meta/header controls indexing. Absence of a rule means allowed — never infer
  a block that is not explicitly stated.
- `Sitemap:` directives are read here too.

## AI crawler matrix (training vs retrieval kept separate)

Different bots have different purposes. We record each bot's role alongside its
disallowed status so a *training opt-out* is never misreported as a *search
visibility defect* (and vice versa):

| Bot | Role | Blocking consequence |
|-----|------|----------------------|
| `OAI-SearchBot` | retrieval | not cited in ChatGPT search |
| `Claude-SearchBot` / `anthropic-ai` | retrieval | not cited in Claude search |
| `PerplexityBot` | retrieval | not cited in Perplexity answers |
| `GPTBot`, `ClaudeBot` | training | excluded from model training |
| `Google-Extended` | training | excludes Gemini training/grounding only — **no effect on Google Search or AI Overviews**, not a ranking signal |
| `Applebot-Extended`, `CCBot` | training | excluded from training corpora |

Semantics: only *retrieval-role* bots being blocked is treated as a visibility
defect; *training-role* blocking is recorded but not flagged as a defect.

## Sitemap

- A 404 or missing `Sitemap:` when `/sitemap.xml` is absent is a
  **recommendation**, not a defect.
- Canonical disagreements are only findings when corroborated (e.g. the sitemap
  also lists the canonical target); otherwise they are informational.

## Canonical, noindex, X-Robots-Tag

- `noindex` (meta robots or X-Robots-Tag) → defect: page excluded from indexes.
- `rel=canonical` is a hint, not a verdict; only assert a cross-host canonical
  when an independent signal (sitemap) agrees.

## What is deliberately NOT flagged here

- Missing JSON-LD on its own → handled by entity-content-audit.
- `/llms.txt` absence → optional experiment, not a defect (Google does not use
  it for AI Overviews / AI Mode).
- JavaScript rendering choice per se → only missing content in the initial HTML
  is a risk.
