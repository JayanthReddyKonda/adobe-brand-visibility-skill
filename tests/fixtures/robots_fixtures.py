"""Robots.txt content fixtures."""

PERMISSIVE_ROBOTS_TXT = """User-agent: *
Allow: /
Sitemap: https://example.com/sitemap.xml
"""

BLOCKING_RETRIEVAL_BOTS_ROBOTS_TXT = """User-agent: *
Allow: /

User-agent: OAI-SearchBot
Disallow: /

User-agent: Claude-SearchBot
Disallow: /

User-agent: PerplexityBot
Disallow: /
"""

BLOCKING_TRAINING_ONLY_ROBOTS_TXT = """User-agent: *
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: CCBot
Disallow: /
"""

RFC9309_SPECIFICITY_ROBOTS_TXT = """User-agent: *
Disallow: /api/
Allow: /api/v1/public/
Disallow: /private/

User-agent: Googlebot
Allow: /api/
"""

MALFORMED_ROBOTS_TXT = """This is not valid robots syntax
Random content
Allow without user-agent: /
Disallow:
"""
