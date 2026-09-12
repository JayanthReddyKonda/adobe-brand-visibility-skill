"""High-performance Zero-Dependency Web Acquisition Engine and Agent Query API.

Coordinates Budget, Security Policy, Robots Auditor, Sitemap Discoverer,
Priority Frontier, Streaming Parser, and Evidence Extractor.
Exposes high-level Agent API primitives (map_site, fetch_page, find_pages, get_page_evidence).
Pure Python standard library (concurrent.futures, urllib.parse, datetime).
"""

from __future__ import annotations

import concurrent.futures
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from .budget import Budget
from .canonical import CanonicalValidator
from .classify import PageClassifier
from .evidence import EvidenceExtractor
from .fetch import SafeFetcher
from .frontier import Frontier
from .jsonld import JsonLdExtractor
from .links import LinkProcessor
from .metadata import MetadataProcessor
from .models import ClaimCandidate, EvidenceModel, FactCandidate, Observation, PageModel
from .policy import SecurityPolicy
from .robots import RobotsAuditor, RobotsOutcome
from .sitemap import SitemapParser


class WebAuditEngine:
    """Master web acquisition orchestrator and agent-facing retrieval interface."""

    def __init__(
        self,
        time_limit_sec: float = 120.0,
        max_pages: int = 25,
        max_depth: int = 3,
        max_concurrency: int = 6,
        user_agent: Optional[str] = None,
        allow_private_ips: bool = False,
        strict_robots: bool = False,
    ) -> None:
        self.max_depth = max_depth
        self.strict_robots = strict_robots
        self.budget = Budget(
            time_limit_sec=time_limit_sec,
            max_pages=max_pages,
            max_depth=max_depth,
            max_concurrency=max_concurrency,
        )
        self.policy = SecurityPolicy(allow_private_ips=allow_private_ips)
        self.fetcher = SafeFetcher(
            policy=self.policy, budget=self.budget, user_agent=user_agent
        )
        self.frontier = Frontier(max_capacity=1000)

        # Audit state
        self.site_url: str = ""
        self.robots_auditor: Optional[RobotsAuditor] = None
        self.pages: List[PageModel] = []
        self.observations: List[Observation] = []
        self.all_facts: List[FactCandidate] = []
        self.all_claims: List[ClaimCandidate] = []
        self.llms_txt_content: Optional[str] = None
        self.llms_full_txt_content: Optional[str] = None
        self.pricing_manifest_content: Optional[str] = None
        self.pricing_manifest_status: int = 404
        self.ai_plugin_content: Optional[str] = None
        self.ai_plugin_status: int = 404
        self.security_txt_content: Optional[str] = None
        self.security_txt_status: int = 404

    def crawl(self, seed_url: str) -> EvidenceModel:
        """Executes a full, bounded, prioritized audit crawl of the target website."""
        norm_seed = LinkProcessor.normalize_url(seed_url)
        if not norm_seed:
            raise ValueError(f"Invalid seed URL: {seed_url}")

        self.site_url = norm_seed
        parsed = urlparse(self.site_url)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        # Step 1: Discover & Audit robots.txt with distinct RFC 9309 status classification
        robots_url = urljoin(base_origin, "/robots.txt")
        declared_sitemaps: List[str] = []
        try:
            robots_res = self.fetcher.fetch(robots_url, timeout=5.0)
            robots_content = robots_res.body_bytes.decode("utf-8", errors="replace")
            if robots_res.status == 200:
                outcome = RobotsOutcome.OK
            elif robots_res.status == 404:
                outcome = RobotsOutcome.NOT_FOUND
            elif robots_res.status in (401, 403):
                outcome = RobotsOutcome.BLOCKED
            elif robots_res.status == 429 or robots_res.status >= 500:
                outcome = RobotsOutcome.SERVER_ERROR
            else:
                outcome = RobotsOutcome.SERVER_ERROR

            self.robots_auditor = RobotsAuditor(
                content=robots_content,
                status_code=robots_res.status,
                outcome=outcome,
            )
            declared_sitemaps.extend(self.robots_auditor.sitemaps)
        except Exception:
            self.robots_auditor = RobotsAuditor(outcome=RobotsOutcome.TIMEOUT)

        # Enforce strict robots if specified
        if self.strict_robots and self.robots_auditor and not self.robots_auditor.is_allowed("BrandAuditBot", self.site_url):
            self.observations.append(
                Observation(
                    type="crawler_access",
                    value="robots_disallow_seed",
                    confidence="high",
                    evidence=f"Seed URL {self.site_url} is blocked by robots.txt under strict mode",
                    severity_hint="critical",
                )
            )
            crawled_at = datetime.now(timezone.utc).isoformat()
            return EvidenceModel(
                site=self.site_url,
                crawled_at=crawled_at,
                pages=[],
                observations=self.observations,
                facts=[],
                scrapeability_summary={},
            )

        # Step 2: Proactive discovery of /llms.txt, /llms-full.txt, and pricing manifests
        self._check_llms_txt(base_origin)

        # Step 3: Discover Sitemaps
        if not declared_sitemaps:
            declared_sitemaps.append(urljoin(base_origin, "/sitemap.xml"))

        sitemap_urls = self._discover_sitemap_urls(declared_sitemaps)
        for sm_url in sitemap_urls:
            norm_sm = LinkProcessor.normalize_url(sm_url)
            if norm_sm and LinkProcessor.is_same_origin(base_origin, norm_sm):
                self.frontier.push(norm_sm, depth=1, is_sitemap_declared=True)

        # Step 4: Enqueue Seed URL
        self.frontier.push(self.site_url, depth=0)

        # Step 5: Bounded Concurrent Fetching Loop with Hard Monotonic Deadline Enforcement
        workers = min(self.budget.max_concurrency, 6)
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        active_futures: Dict[concurrent.futures.Future[Optional[PageModel]], str] = {}

        try:
            while (self.frontier.size() > 0 or active_futures) and not self.budget.is_exhausted():
                if self.budget.remaining_time() <= 0:
                    break

                # Fill worker slots from frontier using atomic slot reservation
                while len(active_futures) < workers and not self.frontier.is_empty():
                    item = self.frontier.pop()
                    if not item:
                        break
                    if not self.budget.reserve_page_slot(item.depth):
                        continue

                    # Check robots.txt permissions
                    if self.robots_auditor and not self.robots_auditor.is_allowed("BrandAuditBot", item.url):
                        self.budget.release_page_slot()
                        self.observations.append(
                            Observation(
                                type="crawler_access",
                                value="robots_disallow",
                                confidence="high",
                                evidence=f"URL {item.url} is blocked by robots.txt directives",
                                severity_hint="high",
                            )
                        )
                        continue

                    fut = executor.submit(self._fetch_and_parse_page, item.url, item.depth, base_origin)
                    active_futures[fut] = item.url

                if not active_futures:
                    break

                # Bounded wait with remaining time ceiling
                wait_sec = max(0.05, min(0.5, self.budget.remaining_time()))
                if self.budget.remaining_time() <= 0:
                    break

                done, _ = concurrent.futures.wait(
                    active_futures.keys(), timeout=wait_sec, return_when=concurrent.futures.FIRST_COMPLETED
                )

                for fut in done:
                    completed_url = active_futures.pop(fut)
                    try:
                        page_model = fut.result()
                        if page_model:
                            self.budget.commit_page_slot()
                            self.pages.append(page_model)
                            self.all_facts.extend(page_model.facts)
                            self.all_claims.extend(page_model.claims)
                            self.observations.extend(page_model.observations)

                            # Enqueue child links
                            if page_model.links and page_model.status == 200:
                                next_depth = page_model.fetch_telemetry.get("depth", 0) + 1
                                for link in page_model.links:
                                    if link.is_internal and LinkProcessor.is_crawlable_html_url(link.href):
                                        self.frontier.push(link.href, depth=next_depth, source_url=page_model.url)
                        else:
                            self.budget.release_page_slot()

                    except Exception as e:
                        self.budget.release_page_slot()
                        self.observations.append(
                            Observation(
                                type="fetch_failure",
                                value="crawl_exception",
                                confidence="high",
                                evidence=f"Processing failed for {completed_url}: {e}",
                                severity_hint="medium",
                            )
                        )
        finally:
            # Release any uncompleted reservations and shutdown
            for _ in active_futures:
                self.budget.release_page_slot()
            active_futures.clear()
            executor.shutdown(wait=False, cancel_futures=True)

        # Build aggregate EvidenceModel
        crawled_at = datetime.now(timezone.utc).isoformat()
        scrapeability = self._compile_scrapeability_summary()
        return EvidenceModel(
            site=self.site_url,
            crawled_at=crawled_at,
            pages=self.pages,
            observations=self.observations,
            facts=self.all_facts,
            claims=self.all_claims,
            scrapeability_summary=scrapeability,
        )

    def _check_llms_txt(self, base_origin: str) -> None:
        """Proactively checks for /llms.txt, /llms-full.txt, pricing manifests, ai-plugin.json, and security.txt."""
        for path in ["/llms.txt", "/llms-full.txt"]:
            target = urljoin(base_origin, path)
            try:
                res = self.fetcher.fetch(target, timeout=4.0)
                if res.status == 200 and len(res.body_bytes) > 20:
                    text = res.body_bytes.decode("utf-8", errors="replace")
                    if path == "/llms.txt":
                        self.llms_txt_content = text
                    else:
                        self.llms_full_txt_content = text
            except Exception:
                pass

        for path in ["/pricing.md", "/pricing.txt"]:
            target = urljoin(base_origin, path)
            try:
                res = self.fetcher.fetch(target, timeout=4.0)
                if res.status == 200 and len(res.body_bytes) > 20:
                    self.pricing_manifest_content = res.body_bytes.decode("utf-8", errors="replace")
                    self.pricing_manifest_status = 200
                    break
            except Exception:
                pass

        # Proactively probe OpenAI AI plugin manifest
        ai_plugin_target = urljoin(base_origin, "/.well-known/ai-plugin.json")
        try:
            res = self.fetcher.fetch(ai_plugin_target, timeout=4.0)
            if res.status == 200 and len(res.body_bytes) > 10:
                self.ai_plugin_content = res.body_bytes.decode("utf-8", errors="replace")
                self.ai_plugin_status = 200
        except Exception:
            pass

        # Proactively probe RFC 9116 security.txt
        for path in ["/.well-known/security.txt", "/security.txt"]:
            target = urljoin(base_origin, path)
            try:
                res = self.fetcher.fetch(target, timeout=4.0)
                if res.status == 200 and len(res.body_bytes) > 10:
                    self.security_txt_content = res.body_bytes.decode("utf-8", errors="replace")
                    self.security_txt_status = 200
                    break
            except Exception:
                pass

    def _discover_sitemap_urls(self, seed_sitemaps: List[str]) -> List[str]:
        """Collects URLs declared in XML sitemaps, validating same-origin to prevent external sitemap probing."""
        discovered: List[str] = []
        base_parsed = urlparse(self.site_url)
        base_host = (base_parsed.hostname or "").lower()

        for sm_url in seed_sitemaps[:3]:
            sm_parsed = urlparse(sm_url)
            if (sm_parsed.hostname or "").lower() != base_host:
                continue
            try:
                res = self.fetcher.fetch(sm_url, timeout=5.0)
                if res.status == 200:
                    xml_text = res.body_bytes.decode("utf-8", errors="replace")
                    urls, child_sitemaps = SitemapParser.parse_sitemap(xml_text)
                    for u in urls[:100]:
                        u_parsed = urlparse(u.loc)
                        if (u_parsed.hostname or "").lower() == base_host:
                            discovered.append(u.loc)
                    # Follow first 2 child sitemaps if index (validating origin)
                    for child in child_sitemaps[:2]:
                        c_parsed = urlparse(child)
                        if (c_parsed.hostname or "").lower() != base_host:
                            continue
                        try:
                            c_res = self.fetcher.fetch(child, timeout=5.0)
                            if c_res.status == 200:
                                c_xml = c_res.body_bytes.decode("utf-8", errors="replace")
                                c_urls, _ = SitemapParser.parse_sitemap(c_xml)
                                for u in c_urls[:50]:
                                    u_parsed = urlparse(u.loc)
                                    if (u_parsed.hostname or "").lower() == base_host:
                                        discovered.append(u.loc)
                        except Exception:
                            continue
            except Exception:
                continue
        return discovered

    def _fetch_and_parse_page(self, url: str, depth: int, base_origin: str) -> Optional[PageModel]:
        """Fetches, parses, extracts, and enriches a single web page."""
        if self.budget.remaining_time() <= 0:
            return None
        try:
            res = self.fetcher.fetch(url)
        except Exception:
            return None

        # P1-14: Separate resource_status from page_status; only status 200 HTML can become a normal page
        if res.status != 200:
            return None

        # Only parse genuine HTML content (prevent non-HTML binaries with .html suffix)
        ct_lower = (res.content_type or "").lower()
        is_html = any(t in ct_lower for t in ("text/html", "application/xhtml+xml"))
        if not is_html:
            sample_prefix = res.body_bytes[:512].lower()
            if b"<html" in sample_prefix or b"<!doctype html" in sample_prefix:
                is_html = True
        if not is_html:
            return None

        # Multi-stage resilient HTML decoding with BOM stripping
        raw_bytes = res.body_bytes
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            raw_bytes = raw_bytes[3:]
        elif raw_bytes.startswith(b"\xff\xfe") or raw_bytes.startswith(b"\xfe\xff"):
            raw_bytes = raw_bytes[2:]

        charset = None
        ct = res.headers.get("content-type", "")
        if "charset=" in ct:
            charset = ct.split("charset=")[-1].split(";")[0].strip().strip("\"'")
        if not charset:
            meta_m = re.search(rb'<meta[^>]+charset=["\']?([a-zA-Z0-9_-]+)', raw_bytes[:1024], re.IGNORECASE)
            if meta_m:
                try:
                    charset = meta_m.group(1).decode("ascii")
                except Exception:
                    pass

        html_text = ""
        if charset:
            try:
                html_text = raw_bytes.decode(charset, errors="replace")
            except Exception:
                pass
        if not html_text:
            try:
                html_text = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                html_text = raw_bytes.decode("latin-1")
        html_text = html_text.replace("\ufeff", "")

        # Step 1: Streaming HTML Parse
        from .parser import StreamingHTMLParser

        parser = StreamingHTMLParser()
        try:
            parser.feed(html_text)
        except Exception:
            pass  # Resilient parsing continues on partial feeds

        x_robots = parser.parse_http_headers(res.headers)

        # Step 2: Extract metadata and JSON-LD
        metadata, meta_obs = MetadataProcessor.process_metadata(parser.meta_tags, source_url=url)
        schemas, jsonld_facts, jsonld_obs = JsonLdExtractor.parse_blocks(
            parser.jsonld_blocks, source_url=url
        )

        # Step 3: Canonical validation
        _, canon_obs = CanonicalValidator.evaluate(url, parser.canonical)

        # Step 4: Links resolution
        resolved_links = LinkProcessor.resolve_and_filter_links(url, parser.raw_links)

        # Step 5: Trafilatura boilerplate stripping, SNR, and Contact/Social extraction
        clean_text = EvidenceExtractor.strip_boilerplate(html_text)
        snr = EvidenceExtractor.calculate_snr(clean_text, html_text)
        render_obs = EvidenceExtractor.detect_rendering_limitations(html_text, clean_text, source_url=url)
        text_facts, claims = EvidenceExtractor.extract_facts_and_claims(clean_text, source_url=url)
        contact_info, social_links = EvidenceExtractor.extract_contact_and_social_info(clean_text, resolved_links)

        # Step 6: LLM-friendly Markdown
        clean_markdown = EvidenceExtractor.build_clean_markdown(
            title=parser.title,
            headings=parser.headings,
            clean_text=clean_text,
            tables=parser.tables,
            code_blocks=parser.code_blocks,
        )

        # Step 7: Classification
        page_type = PageClassifier.classify(
            url=url,
            title=parser.title,
            schemas=schemas,
            headings=[h.text for h in parser.headings],
        )

        page_observations = meta_obs + jsonld_obs + canon_obs + render_obs
        all_page_facts = jsonld_facts + text_facts

        return PageModel(
            url=url,
            final_url=res.final_url,
            redirect_chain=res.redirects,
            status=res.status,
            content_type=res.content_type,
            title=parser.title,
            description=metadata.get("standard", {}).get("description", ""),
            canonical=parser.canonical,
            canonicals=parser.canonicals,
            robots_meta=metadata.get("robots_directives", []),
            x_robots_tag=x_robots,
            language=parser.language,
            hreflangs=parser.hreflangs,
            headings=parser.headings,
            links=resolved_links,
            ctas=parser.ctas,
            social_links=social_links,
            contact_info=contact_info,
            dates=parser.dates,
            jsonld=schemas,
            metadata=metadata,
            clean_text=clean_text,
            clean_markdown=clean_markdown,
            word_count=len(clean_text.split()),
            snr=snr,
            page_type=page_type,
            semantic_landmarks=parser.semantic_landmarks,
            tables=parser.tables,
            code_blocks=parser.code_blocks,
            images=parser.images,
            observations=page_observations,
            facts=all_page_facts,
            claims=claims,
            headers=res.headers,
            fetch_telemetry={
                "latency_ms": res.latency_ms,
                "bytes": len(res.body_bytes),
                "redirects": len(res.redirects),
                "depth": depth,
            },
            raw_html=html_text,
        )

    def _compile_scrapeability_summary(self) -> Dict[str, Any]:
        """Compiles AI agent scrapeability metrics across crawled pages."""
        total_pages = len(self.pages)
        if total_pages == 0:
            return {}

        avg_snr = sum(p.snr for p in self.pages) / float(total_pages)
        pages_with_landmarks = sum(1 for p in self.pages if len(p.semantic_landmarks) >= 2)
        sparse_shells = sum(
            1 for p in self.pages if any(o.value == "server_html_appears_sparse" for o in p.observations)
        )

        return {
            "total_crawled_pages": total_pages,
            "average_snr": round(avg_snr, 4),
            "site_scrapeability_snr": round(avg_snr, 4),
            "snr_health": "good" if avg_snr >= 0.12 else "low",
            "semantic_landmarks_coverage_pct": round((pages_with_landmarks / total_pages) * 100, 1),
            "sparse_spa_shells_count": sparse_shells,
            "llms_txt_present": self.llms_txt_content is not None,
            "llms_full_txt_present": self.llms_full_txt_content is not None,
        }

    # =========================================================================
    # High-Level Agent Query API (Firecrawl / Web Agent inspired)
    # =========================================================================

    def map_site(self) -> List[Dict[str, Any]]:
        """Returns structured map of all crawled pages and page types."""
        return [
            {
                "url": p.url,
                "type": p.page_type.get("value", "unknown"),
                "status": p.status,
                "title": p.title,
                "word_count": p.word_count,
            }
            for p in self.pages
        ]

    def fetch_page(self, url: str) -> Optional[PageModel]:
        """Retrieves an already crawled page model by exact or normalized URL."""
        norm = LinkProcessor.normalize_url(url)
        for p in self.pages:
            if p.url == url or p.url == norm or p.final_url == norm:
                return p
        return None

    def find_pages(self, page_type: str) -> List[PageModel]:
        """Finds all crawled pages matching a specific page type (e.g. 'pricing', 'product_detail')."""
        return [p for p in self.pages if p.page_type.get("value") == page_type]

    def get_page_evidence(self, url: str) -> Dict[str, Any]:
        """Retrieves evidence bundle for a specific page."""
        page = self.fetch_page(url)
        if not page:
            return {}
        return {
            "url": page.url,
            "markdown": page.clean_markdown,
            "facts": [f.to_dict() for f in page.facts],
            "claims": [c.to_dict() for c in page.claims],
            "observations": [o.to_dict() for o in page.observations],
            "snr": page.snr,
        }

    def find_attribute(
        self, attribute: str, entity: Optional[str] = None, source_url: Optional[str] = None
    ) -> List[FactCandidate]:
        """Queries the global fact ledger with optional entity and source scoping."""
        results = [f for f in self.all_facts if f.attribute.lower() == attribute.lower()]
        if entity:
            results = [f for f in results if f.entity and entity.lower() in f.entity.lower()]
        if source_url:
            results = [f for f in results if f.source_url == source_url]
        return results

    def to_inventory_dict(self) -> Dict[str, Any]:
        """Converts crawled site data to backward-compatible inventory JSON format."""
        inv_pages = []
        for p in self.pages:
            ptype_val = p.page_type.get("value", "other") if isinstance(p.page_type, dict) else str(p.page_type)
            pconf_val = p.page_type.get("confidence", 0.8) if isinstance(p.page_type, dict) else 0.8
            parsed_u = urlparse(p.url)
            logical_template = parsed_u.path or "/"

            # Map landmarks to dict of boolean indicators
            landmarks_set = set(p.semantic_landmarks)
            landmarks_dict = {
                "has_main": "main" in landmarks_set,
                "has_article": "article" in landmarks_set,
                "has_header": "header" in landmarks_set,
                "has_nav": "nav" in landmarks_set,
                "has_footer": "footer" in landmarks_set,
            }

            is_spa = any(o.value == "server_html_appears_sparse" for o in p.observations) or (p.snr < 0.08 and p.word_count < 25)

            inv_pages.append(
                {
                    "url": p.url,
                    "final_url": p.final_url,
                    "redirect_chain": p.redirect_chain,
                    "status": p.status,
                    "resource_type": "html",
                    "content_type": p.content_type,
                    "page_type": ptype_val,
                    "page_type_confidence": pconf_val,
                    "logical_template": logical_template,
                    "language": p.language,
                    "locale": None,  # Distinct from language; not defaulted to 'en'
                    "title": p.title,
                    "description": p.description,
                    "canonical": p.canonical,
                    "canonicals": p.canonicals,
                    "robots_meta": p.robots_meta,
                    "x_robots_tag": p.x_robots_tag,
                    "hreflangs": [h.to_dict() for h in p.hreflangs],
                    "h1": [h.text for h in p.headings if h.level == 1],
                    "h2": [h.text for h in p.headings if h.level == 2],
                    "jsonld": p.jsonld,
                    "metadata": p.metadata,
                    "clean_text": p.clean_text,
                    "clean_markdown": p.clean_markdown,
                    "word_count": p.word_count,
                    "snr": p.snr,
                    "text_density_ratio": round(p.snr, 4),
                    "is_sparse_spa": is_spa,
                    "semantic_landmarks": landmarks_dict,
                    "semantic_landmarks_list": p.semantic_landmarks,
                    "internal_links": [link.href for link in p.links if link.is_internal],
                    "external_links": [link.href for link in p.links if not link.is_internal],
                    "ctas": [c.to_dict() for c in p.ctas],
                    "social_links": p.social_links,
                    "contact_info": p.contact_info,
                    "dates": p.dates,
                    "tables": [t.to_dict() for t in p.tables],
                    "code_blocks": p.code_blocks,
                    "images": p.images,
                    "html": p.raw_html,
                    "headers": p.headers,
                    "latency_ms": p.fetch_telemetry.get("latency_ms", 0.0),
                }
            )

        declared_sitemaps = self.robots_auditor.sitemaps if self.robots_auditor else []
        infrastructure_data = {
            "homepage_reachable": any(p.status == 200 for p in self.pages),
            "robots": {
                "status": self.robots_auditor.status_code if self.robots_auditor else 404,
                "text": self.robots_auditor.raw_content if self.robots_auditor and self.robots_auditor.status_code == 200 else None,
            },
            "robots_txt": self.robots_auditor.raw_content if self.robots_auditor else "",
            "robots_status": self.robots_auditor.status_code if self.robots_auditor else 404,
            "robots_outcome": self.robots_auditor.outcome if self.robots_auditor else "robots_not_found",
            "sitemaps_discovered": declared_sitemaps,
            "sitemaps_processed": len(declared_sitemaps),
            "urls_extracted": self.frontier.total_seen(),
            "same_origin_urls": self.frontier.total_seen(),
            "llms_txt": {
                "status": 200 if self.llms_txt_content else 404,
                "present": self.llms_txt_content is not None,
                "is_spec_compliant": bool(re.search(r"^#\s+[^\n]+", self.llms_txt_content or "", re.MULTILINE)),
                "snippet": (self.llms_txt_content[:400] if self.llms_txt_content else None),
            },
            "llms_full_txt": {
                "status": 200 if self.llms_full_txt_content else 404,
                "present": self.llms_full_txt_content is not None,
                "snippet": (self.llms_full_txt_content[:400] if self.llms_full_txt_content else None),
            },
            "pricing_manifest": {
                "status": self.pricing_manifest_status,
                "present": self.pricing_manifest_content is not None,
                "snippet": (self.pricing_manifest_content[:400] if self.pricing_manifest_content else None),
            },
            "ai_plugin": {
                "status": self.ai_plugin_status,
                "present": self.ai_plugin_content is not None,
                "snippet": (self.ai_plugin_content[:400] if self.ai_plugin_content else None),
            },
            "security_txt": {
                "status": self.security_txt_status,
                "present": self.security_txt_content is not None,
                "snippet": (self.security_txt_content[:400] if self.security_txt_content else None),
            },
            "ai_agent_scrapeability_summary": self._compile_scrapeability_summary(),
        }

        robots_matrix: Dict[str, bool] = {}
        if self.robots_auditor:
            raw_matrix = self.robots_auditor.evaluate_ai_bots_matrix("/")
            robots_matrix = {bot: bool(info.get("allowed", True)) for bot, info in raw_matrix.items()}
        total_raw_bytes = sum(len(p.raw_html.encode("utf-8")) for p in self.pages)

        return {
            "site": self.site_url,
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            "homepage": self.site_url,
            "pages_count": len(self.pages),
            "infrastructure": infrastructure_data,
            "robots": {
                "status": self.robots_auditor.status_code if self.robots_auditor else 404,
                "raw": self.robots_auditor.raw_content if self.robots_auditor else "",
                "sitemaps": declared_sitemaps,
                "matrix": robots_matrix,
            },
            "sitemaps": declared_sitemaps,
            "robots_txt": self.robots_auditor.raw_content if self.robots_auditor else "",
            "robots_status": self.robots_auditor.status_code if self.robots_auditor else 404,
            "robots_outcome": self.robots_auditor.outcome if self.robots_auditor else "robots_not_found",
            "llms_txt": self.llms_txt_content,
            "llms_full_txt": self.llms_full_txt_content,
            "ai_plugin": self.ai_plugin_content,
            "security_txt": self.security_txt_content,
            "ai_agent_scrapeability_summary": self._compile_scrapeability_summary(),
            "pages": inv_pages,
            "all_facts": [f.to_dict() for f in self.all_facts],
            "all_claims": [c.to_dict() for c in self.all_claims],
            "stats": {
                "pages_crawled": len(self.pages),
                "total_bytes": total_raw_bytes,
                "elapsed_seconds": round(self.budget.elapsed_time(), 2),
                "average_latency_ms": round(sum(p.fetch_telemetry.get("latency_ms", 0.0) for p in self.pages) / max(len(self.pages), 1), 2),
                "total_facts": len(self.all_facts),
                "total_claims": len(self.all_claims),
            },
            "limitations": [],
            "elapsed_seconds": round(self.budget.elapsed_time(), 1),
        }
