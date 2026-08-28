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
# Run full composed audit (real network checks) and write the JSON report
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py --site example.com --output report.json

# To present the report in chat (stdout) without writing a file
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/orchestrator.py --site example.com

# Validate report against the official schema
python3 brand-ai-readiness-audit/skills/audit-orchestrator/scripts/validate_report.py report.json
```

### 2. Natural Language / Agent Prompt Triggering

In any compatible agent (Antigravity, Claude Code, Junie, OpenHands, VS Code), prompt:

> *"Audit https://example.com for AI discoverability and on-site engagement and emit the final JSON report."*

The agent discovers `audit-orchestrator` via `SKILL.md` description matching, activates the skill, executes the underlying specialist tools, and returns the schema-compliant JSON report as its **only** output — the report is presented directly in chat as raw JSON, with no accompanying prose. A file is written only if the user explicitly requests one.
