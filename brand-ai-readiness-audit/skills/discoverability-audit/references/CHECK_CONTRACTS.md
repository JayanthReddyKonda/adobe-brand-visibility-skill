# Discoverability Audit — Check Contracts

Every check in this skill states what it measures, what evidence is required,
what does **not** constitute a defect, and how severity is assigned. Checks
never report a finding without direct evidence gathered during this run.

## C1. Homepage reachability
- **Measures:** HTTP status of the homepage fetch.
- **Defect:** Non-200 response (fetch failures are `status: inconclusive`, not defects).
- **Severity:** `critical` on non-200 — AI crawlers cannot retrieve any content.
- **Not a defect:** Slow but successful responses (latency is out of scope).

## C2. robots.txt AI-crawler access (RFC 9309)
- **Measures:** Longest-match robots.txt evaluation for GPTBot, OAI-SearchBot,
  ClaudeBot, PerplexityBot, Google-Extended against `/`, honoring
  `User-agent: *` fallback groups per RFC 9309 semantics.
- **Defect:** A rule disallows a listed AI crawler where a generic browser
  group would be allowed.
- **Severity:** `high` (downgraded to `medium` if only one minor crawler is blocked).
- **Not a defect:** No robots.txt at all (absence means allow-all); blocking
  aggressive non-search scrapers; blocking paths the homepage doesn't rely on.

## C3. Differential UA treatment
- **Measures:** Whether AI-crawler user-agents receive materially different
  responses than a generic browser UA (status or body length).
- **Defect:** Consistent, meaningful divergence across UAs.
- **Severity:** `high`, confidence `medium` (CDN quirks can cause false
  divergence; hence medium confidence and worded as "treatment differs").

## C4. noindex / X-Robots-Tag
- **Measures:** `meta robots` and `X-Robots-Tag` headers for `noindex`/`none`.
- **Defect:** Directive present on a public page.
- **Severity:** `critical` — an explicit machine instruction to be excluded.

## C5. Canonical consistency (corroborated)
- **Measures:** Canonical link target vs. requested host, cross-checked
  against redirect behavior and sitemap entries.
- **Defect:** Reported **only when** the canonical target is corroborated by
  a second signal (redirect chain or sitemap). Canonical alone is a hint,
  not a verdict.
- **Severity:** `medium`, confidence `high` (because corroborated).

## C6. Rendering risk
- **Measures:** Visible word count of the initial HTML and presence of an
  empty SPA root container.
- **Defect:** Very low word count **plus** SPA root marker → high (rendering
  risk for non-JS crawlers). Very low word count without the marker → low,
  phrased as a verification prompt rather than a proven gap.
- **Not a defect:** This check never claims the page "cannot render" — only
  what is (or is not) present in the initial HTML, which is what non-JS
  crawlers actually see.

## Inconclusive handling
If the homepage cannot be fetched, the script returns
`status: "inconclusive"` with zero findings. The orchestrator surfaces this
status; it is never interpreted as "clean".
