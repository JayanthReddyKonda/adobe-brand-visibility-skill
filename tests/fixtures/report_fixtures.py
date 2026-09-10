"""Audit report fixtures for Draft-07 schema validation testing."""

VALID_SCHEMA_REPORT = {
    "schema_version": "1.0.0",
    "site": "https://example.com",
    "audited_at": "2026-09-06T12:00:00Z",
    "audit_status": "complete",
    "summary": {
        "total_findings": 1,
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
    },
    "findings": [
        {
            "id": "finding-1",
            "title": "Robots.txt blocks AI SearchBot retrieval",
            "severity": "high",
            "category": "discoverability",
            "root_cause": "User-agent Disallow directive",
            "confidence": "high",
            "scope": "robots.txt",
            "evidence": {
                "summary": "Disallow: / found for OAI-SearchBot",
                "scope": "robots.txt",
                "sources": [
                    {
                        "url": "https://example.com/robots.txt",
                        "type": "robots_txt",
                        "observation": "Disallow: /",
                    }
                ],
            },
            "impact": "Impairs AI crawler indexation, causing the domain or catalog to be omitted from AI search retrieval.",
            "suggested_action": {
                "summary": "Allow AI search bots in robots.txt",
                "priority": "high",
                "technical_fix": "Add 'Allow: /' under 'User-agent: OAI-SearchBot'",
                "creative_fix": None,
                "verification": "Check robots.txt response with curl",
            },
        }
    ],
    "proactive_actions": [
        {
            "id": "action-1",
            "title": "Deploy structured llms.txt manifest",
            "summary": "Deploy an llms.txt manifest at the site root to facilitate LLM citations.",
            "priority": "medium",
            "technical_fix": "Create /llms.txt at root with markdown index",
            "creative_fix": "Provide concise executive summaries for LLM citation",
            "verification": "HTTP 200 on /llms.txt",
        }
    ],
}

VALID_STRING_EVIDENCE_REPORT = {
    "schema_version": "1.0.0",
    "site": "https://example.com",
    "audited_at": "2026-09-06T12:00:00Z",
    "audit_status": "complete",
    "summary": {
        "total_findings": 1,
        "critical": 1,
        "high": 0,
        "medium": 0,
        "low": 0,
    },
    "findings": [
        {
            "id": "finding-1",
            "title": "Meta noindex on homepage",
            "severity": "critical",
            "category": "discoverability",
            "root_cause": "noindex meta tag present",
            "confidence": "high",
            "scope": "https://example.com/",
            "evidence": "Found <meta name='robots' content='noindex'> on homepage",
            "impact": "Prevents AI search engines from indexing the homepage.",
            "suggested_action": {
                "summary": "Remove noindex tag",
                "priority": "critical",
                "technical_fix": "Remove meta robots noindex tag from index.html",
                "creative_fix": None,
                "verification": "Inspect HTML response headers and meta tags",
            },
        }
    ],
    "proactive_actions": [],
}

INVALID_SEVERITY_REPORT = {
    "schema_version": "1.0.0",
    "site": "https://example.com",
    "audited_at": "2026-09-06T12:00:00Z",
    "audit_status": "complete",
    "summary": {
        "total_findings": 1,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
    },
    "findings": [
        {
            "id": "finding-1",
            "title": "Minor warning",
            "severity": "info",  # Forbidden by Draft-07 schema
            "category": "discoverability",
            "root_cause": "Test",
            "confidence": "low",
            "scope": "https://example.com/",
            "evidence": "Test evidence",
            "impact": "Minor observation impact.",
            "suggested_action": {
                "summary": "Fix",
                "priority": "low",
                "technical_fix": "Fix it",
                "creative_fix": None,
                "verification": "Verify",
            },
        }
    ],
    "proactive_actions": [],
}

MISSING_REQUIRED_FIELD_REPORT = {
    "site": "https://example.com",
    # Missing audited_at, summary, findings
}

NON_INTEGER_SUMMARY_REPORT = {
    "schema_version": "1.0.0",
    "site": "https://example.com",
    "audited_at": "2026-09-06T12:00:00Z",
    "audit_status": "complete",
    "summary": {
        "total_findings": "1",  # String instead of integer
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
    },
    "findings": [],
    "proactive_actions": [],
}
