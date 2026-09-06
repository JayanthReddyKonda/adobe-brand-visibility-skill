"""Sitemap XML content fixtures."""

import gzip

VALID_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2026-09-01T00:00:00Z</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.com/pricing</loc>
        <lastmod>2026-09-01T00:00:00Z</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>
"""

VALID_SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://example.com/sitemap1.xml</loc>
        <lastmod>2026-09-01</lastmod>
    </sitemap>
</sitemapindex>
"""

MALFORMED_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/broken
    <!-- missing closing tags -->
"""


def get_gzipped_sitemap_bytes():
    return gzip.compress(VALID_SITEMAP_XML.encode("utf-8"))
