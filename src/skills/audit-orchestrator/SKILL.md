---
name: brand-ai-readiness-audit
description: The master Orchestrator Agent Skill. Instructs the AI Agent on how to execute all sensory tools, gather pure diagnostic telemetry, apply cognitive reasoning to deduce root causes, and synthesize a Draft-07 schema-compliant JSON report.
license: MIT
---
# Brand AI-Readiness Audit (True Agentic Architecture)

## When to use
Use this when the user asks to "audit a website for AI discoverability and engagement".

## Inputs
- `site` (string): The URL or domain to audit.

## Procedure

> [!IMPORTANT]
> **EVALUATOR MANDATE:** As the True Agentic Orchestrator, YOU must orchestrate the tools and perform the synthesis. The scripts are strictly sensory tools—they no longer pre-bake findings or recommendations.

### Step 1: Inventory Acquisition
Execute the inventory script to crawl the site and gather HTML pages:
```bash
python3 skills/audit-orchestrator/scripts/acquire_inventory.py --site https://example.com --output /tmp/inv.json --format json
```

### Step 2: Diagnostic Telemetry Probes
Execute each of the specialist tools sequentially. Each returns a `TelemetryResponse` (JSON).

1. **Discoverability:** `python3 skills/discoverability-audit/scripts/discoverability_check.py --site https://example.com --inventory /tmp/inv.json`
2. **Entity Content:** `python3 skills/entity-content-audit/scripts/entity_content_check.py --site https://example.com --inventory /tmp/inv.json`
3. **Fact Consistency:** `python3 skills/fact-consistency-audit/scripts/fact_consistency_check.py --site https://example.com --inventory /tmp/inv.json`
4. **Authority Corroboration:** `python3 skills/corroboration-authority-audit/scripts/corroboration_check.py --site https://example.com --inventory /tmp/inv.json`
5. **GEO Content:** `python3 skills/geo-content-audit/scripts/geo_content_check.py --site https://example.com --inventory /tmp/inv.json`
6. **Engagement Context:** `python3 skills/engagement-context-audit/scripts/engagement_check.py --site https://example.com --inventory /tmp/inv.json`

### Step 3: AI Cognitive Reasoning
1. **Analyze:** Review the `raw_extracted_facts` and `telemetry` from all tools.
2. **Synthesize Findings:** For each problematic fact (e.g., missing schema, blocked crawlers, shallow mechanisms), deduce the `severity`, `root_cause`, and `impact`.
3. **Tailor Recommendations:** Write bespoke `technical_fix` and `creative_fix` solutions that perfectly match the brand's context.

### Step 4: Output Synthesis & Validation
Construct the final Draft-07 schema-compliant JSON report.
Save it to `/tmp/final_report.json` and validate:
```bash
python3 skills/audit-orchestrator/scripts/validate_report.py < /tmp/final_report.json
```

## Output
If validation passes, emit a beautiful Executive Summary of the issues followed by the raw JSON report in a `json` markdown block.
