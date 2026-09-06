"""JSON-LD structured data fixtures."""

VALID_ORGANIZATION_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Enterprise AI Cloud",
    "url": "https://example.com",
    "logo": "https://example.com/logo.png",
    "description": "High-performance autonomous infrastructure provider.",
    "sameAs": [
        "https://www.wikidata.org/wiki/Q115000",
        "https://www.linkedin.com/company/enterprise-ai-cloud",
        "https://en.wikipedia.org/wiki/Enterprise_AI_Cloud",
    ],
    "contactPoint": {
        "@type": "ContactPoint",
        "telephone": "+1-800-555-0100",
        "contactType": "customer service",
        "email": "support@example.com",
    },
}

VALID_PRODUCT_WITH_OFFER_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Enterprise Cloud Cluster",
    "description": "Autonomous cloud cluster for developer teams.",
    "brand": {
        "@type": "Brand",
        "name": "Enterprise AI Cloud",
    },
    "offers": {
        "@type": "Offer",
        "price": "49.00",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
        "url": "https://example.com/pricing",
    },
}

VALID_GRAPH_JSONLD = {
    "@context": "https://schema.org",
    "@graph": [
        VALID_ORGANIZATION_JSONLD,
        VALID_PRODUCT_WITH_OFFER_JSONLD,
    ],
}

PRODUCT_MISSING_SPECS_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Product",
    "name": "Mystery Product",
}

CIRCULAR_SAMEAS_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Self Referencing Org",
    "url": "https://example.com",
    "sameAs": [
        "https://example.com/",
        "https://example.com/about",
    ],
}

MALFORMED_JSONLD_RAW = """{
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Broken Quotes",
    "url": "https://example.com",,,
}"""
