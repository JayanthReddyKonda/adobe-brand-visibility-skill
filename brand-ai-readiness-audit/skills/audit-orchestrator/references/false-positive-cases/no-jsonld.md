# False Positive Decision Table: Absence of JSON-LD Schema

## Signal
Page contains readable HTML text but has no `<script type="application/ld+json">` blocks.

## Do NOT Report As Defect When:
- The page is a standard informational or blog article where `<title>`, `<h1>`, and OpenGraph meta tags clearly state the entity identity.
- The visible text is explicit and unambiguous for human and AI readers.
- The site is crawlable and has no ranking or factual ambiguity issues.

## Report ONLY As:
- **Proactive Recommendation (`proactive_actions[]`)**: Suggesting structured data to enhance machine extraction and rich snippet eligibility.

## Report As Defect ONLY When:
- The page is a core commercial flagship product or organization page where crucial facts (pricing variants, availability state, technical specifications) are embedded in complex client-side tables or obfuscated structures that cannot be extracted deterministically without structured schema.

