# Brand AI-Readiness Audit Marketplace

**Adobe University Hackathon 2026 — Round 3**

An agentic AI skill marketplace built in the standard [agentskills.io](https://agentskills.io) specification. Audits websites for **AI Discoverability** (ChatGPT, Claude, Gemini, Perplexity crawling and citations) and **On-Site Engagement** (visitor orientation and bounce prevention), outputting an evidence-backed audit report.

---

## 📁 Repository Layout

```text
.
├── brand-ai-readiness-audit/               # Primary marketplace package (submission root)
│   ├── marketplace.json                    # Manifest listing skills & designated entrypoint
│   ├── README.md                           # Marketplace overview & composition architecture
│   └── skills/
│       ├── audit-orchestrator/             # [ENTRYPOINT] Composes specialist skills & emits JSON report
│       ├── crawl-render-audit/             # [SPECIALIST] Crawlability, JS rendering & Schema.org JSON-LD
│       ├── freshness-corroboration/        # [SPECIALIST] Fact staleness, update dates & sameAs entity links
│       └── engagement-audit/               # [SPECIALIST] Orientation, heading hierarchy & AI summaries
└── .agents/skills/                         # Mirrored skills for active agent client discovery (.gitignore'd)
```

---

## 🚀 How to Test and Invoke the Skills

### 1. Direct Command-Line Execution (Cross-Platform)

```bash
# Run full composed audit in mock verification mode
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py --site example.com --mock --output report.json

# Validate report against the official schema
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/validate_report.py report.json
```

### 2. Natural Language / Agent Prompt Triggering

In any compatible agent (Antigravity, Claude Code, Junie, OpenHands, VS Code), prompt:

> *"Audit https://example.com for AI discoverability and on-site engagement and emit the final JSON report."*

The agent discovers `audit-orchestrator` via `SKILL.md` description matching, activates the skill, executes the underlying specialist tools, and emits the schema-compliant report.

### 3. Using Chat Slash Commands

The skill ships two real slash commands (defined in `skills/audit-orchestrator/commands/`):

- **`/audit <site-url-or-domain>`** — Run a full AI brand visibility and engagement audit:
  ```text
  /audit https://example.com
  ```
  Composes the specialist skills, reconciles findings, and emits the schema-compliant JSON report.

- **`/validate <path-to-report.json>`** — Validate an existing audit report against the official schema:
  ```text
  /validate report.json
  ```

> Slash commands are surfaced by the agent client. If they don't appear in your client's `/` palette, ensure the skill is registered for discovery by that client (e.g. the `.agents/skills/` mirror for OMO/OpenCode), then restart the client so it re-scans the skill.
