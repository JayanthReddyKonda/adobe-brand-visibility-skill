"""HTML fixtures for unit and integration testing."""

CLEAN_ENTERPRISE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Enterprise AI Cloud - High Performance Autonomous Infrastructure</title>
    <meta name="description" content="Enterprise AI Cloud provides scalable autonomous infrastructure for high-throughput computing.">
    <link rel="canonical" href="https://example.com/">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Enterprise AI Cloud",
        "url": "https://example.com",
        "sameAs": [
            "https://www.wikidata.org/wiki/Q115000",
            "https://www.linkedin.com/company/enterprise-ai-cloud",
            "https://en.wikipedia.org/wiki/Enterprise_AI_Cloud"
        ]
    }
    </script>
</head>
<body>
    <header>
        <nav><a href="/">Home</a> <a href="/pricing">Pricing</a></nav>
    </header>
    <main>
        <h1>Enterprise AI Cloud Infrastructure</h1>
        <p>Accelerate neural model deployments by 74% because distributed low-latency clusters eliminate bottlenecks.</p>
        <p>According to Dr. Elizabeth Vance, Chief Architect at MIT Systems Lab,
        "Predictive memory pooling improves throughput by 3.4x under heavy concurrency."</p>
        <a href="/pricing" class="btn-primary">View Plans and Pricing</a>
        <section>
            <h2>Performance Specifications</h2>
            <table>
                <thead><tr><th>Metric</th><th>Baseline</th><th>Enterprise Cloud</th></tr></thead>
                <tbody>
                    <tr><td>Throughput (req/sec)</td><td>12,000</td><td>48,500</td></tr>
                    <tr><td>P99 Latency (ms)</td><td>42.5</td><td>4.8</td></tr>
                </tbody>
            </table>
        </section>
    </main>
    <footer>
        <p>&copy; 2026 Enterprise AI Cloud Inc. Contact: support@example.com</p>
    </footer>
</body>
</html>"""

PRICING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Pricing Plans - Enterprise AI Cloud</title>
    <meta name="description" content="Transparent pricing for autonomous computing tiers.">
    <link rel="canonical" href="https://example.com/pricing">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Enterprise Cloud Starter",
        "description": "Autonomous cloud cluster for developer teams.",
        "offers": {
            "@type": "Offer",
            "price": "49.00",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
        }
    }
    </script>
</head>
<body>
    <main>
        <h1>Transparent Enterprise Pricing</h1>
        <p>Our Starter tier is priced at $49.00 per month with zero setup fees.</p>
        <a href="/checkout?tier=starter" class="cta-button">Deploy Starter Cluster</a>
        <table>
            <tr><th>Tier</th><th>Price</th><th>Availability</th></tr>
            <tr><td>Starter</td><td>$49.00 / mo</td><td>Immediate Provisioning</td></tr>
            <tr><td>Pro</td><td>$199.00 / mo</td><td>Immediate Provisioning</td></tr>
        </table>
    </main>
    <footer>
        <p>&copy; 2026 Enterprise AI Cloud Inc. Contact: support@example.com</p>
    </footer>
</body>
</html>"""

CONFLICTING_PRICING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Legacy Pricing - Enterprise AI Cloud</title>
    <link rel="canonical" href="https://example.com/old-pricing">
</head>
<body>
    <main>
        <h1>Legacy Tier Overview</h1>
        <p>Our Starter tier is priced at $99.00 per month with legacy billing.</p>
        <p>Contact support at legacy-billing@example.com or call +1-800-555-0199.</p>
    </main>
    <footer>
        <p>&copy; 2021 Enterprise AI Cloud Inc.</p>
    </footer>
</body>
</html>"""

CSR_EMPTY_SHELL_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Client Rendered Portal</title>
</head>
<body>
    <div id="root"></div>
    <script src="/static/bundle.js"></script>
</body>
</html>"""

NOINDEX_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Staging Environment</title>
    <meta name="robots" content="noindex, nofollow">
</head>
<body>
    <h1>Staging Environment Only</h1>
    <p>Do not crawl or index this environment.</p>
</body>
</html>"""

MISSING_H1_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>No Heading Page</title>
</head>
<body>
    <div class="banner">Welcome to our service</div>
    <p>We offer high quality services with rapid delivery.</p>
    <a href="/buy">Buy Now</a>
</body>
</html>"""

HIDDEN_CTA_HTML = """<!DOCTYPE html>
<html>
<head><title>Long Scroll Page</title></head>
<body>
    <h1>Welcome to the Knowledge Base</h1>
    <nav><a href="/1">1</a><a href="/2">2</a><a href="/3">3</a><a href="/4">4</a><a href="/5">5</a></nav>
    <p>Section 1 text here...</p>
    <a href="/aux1">Auxiliary Link 1</a>
    <a href="/aux2">Auxiliary Link 2</a>
    <a href="/aux3">Auxiliary Link 3</a>
    <a href="/aux4">Auxiliary Link 4</a>
    <a href="/buy" class="main-cta">Purchase Subscription</a>
</body>
</html>"""

HEDGY_TEXT_HTML = """<!DOCTYPE html>
<html>
<head><title>Uncertain Claims</title></head>
<body>
    <h1>Speculative Computing</h1>
    <p>It seems that our system might possibly perform better in certain circumstances.
    We could arguably say that users perhaps experience fewer latency spikes, although it is likely dependent on conditions.</p>
    <p>Maybe the algorithms could be considered relatively fast, and conceivably they may assist somewhat in reducing overhead.</p>
</body>
</html>"""

MALFORMED_HTML = """<!DOCTYPE html>
<html><head><title>Malformed <<<>>> Page</title>
<body>
<p>Unclosed paragraph <div>Nested wrongly <p>Text inside</p>
<script type="application/ld+json">{ broken json }<script>
</body>"""
