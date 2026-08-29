# AI Snippet & Information Scent Guidelines

How to structure on-page content so AI search assistants and human visitors can immediately extract answers and orient without bouncing.

---

## 1. Conclusion-First Writing Architecture

AI models and skimming visitors prioritize direct answers in above-the-fold passages:

- **Direct Answer in Lead Paragraph:** State the core definition, price, or product capability within the first 50–100 words.
- **Fact-Dense Sentences:** Use explicit combinations of `[Subject] + [Attribute] + [Numerical Value/Unit] + [Timeframe]`.
  - *Poor:* "Our revolutionary solution offers unprecedented affordability and power."
  - *Strong:* "The Velocity X9 drone costs ₹5,499, delivers 30 minutes of flight time, and captures 4K 60fps video."

---

## 2. Heading Hierarchy & Information Scent

Headings provide structural boundaries for passage indexing and AI chunking:

- **Single H1 per Page:** The primary `<h1>` must clearly name the brand, product, or core topic. Avoid generic filler titles ("Welcome", "Home", "Overview").
- **Question-Form H2/H3 Headings:** Phrase subheadings as clear questions or explicit topic statements (e.g. `<h2>What is the battery range of Velocity X9?</h2>`).
- **No Skipping Levels:** Maintain a strict logical hierarchy (`H1` -> `H2` -> `H3`). Never skip from `H1` directly to `H4`.

---

## 3. Snippet Visibility Controls

| Directive | Implementation | Effect on AI Answers |
| :--- | :--- | :--- |
| `nosnippet` | `<meta name="robots" content="nosnippet">` | Prevents the page from being quoted in snippets or AI Overviews entirely. |
| `max-snippet` | `<meta name="robots" content="max-snippet:160">` | Restricts snippet quotes to the specified character length. |
| `data-nosnippet` | `<div data-nosnippet>...</div>` | Excludes specific proprietary text or pricing footnotes from AI quotes while keeping the rest indexable. |
