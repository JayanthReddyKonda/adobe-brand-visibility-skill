"""Single-pass streaming HTML parser for multi-signal page extraction.

Collects metadata, headings (H1-H6), hyperlinks, tables, code blocks,
semantic landmark tags, and JSON-LD script bodies without building a heavy DOM tree.
Pure Python standard library (html.parser.HTMLParser).
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

from .models import CTA, Heading, HreflangLink, TableData

COMMERCIAL_CTA_REGEX = re.compile(
    r"\b(buy|order|purchase|checkout|cart|subscribe|sign\s*up|get\s*started|start\s*free|try\s*free|book\s*demo|request\s*demo|contact\s*sales|get\s*quote|pricing|plans|pricing-plans|trial)\b",
    re.IGNORECASE,
)


class StreamingHTMLParser(HTMLParser):
    """Zero-dependency single-pass streaming HTML parser."""

    IGNORE_TAGS = {"script", "style", "noscript", "svg", "canvas", "template", "iframe"}
    LANDMARK_TAGS = {"main", "article", "header", "nav", "footer", "aside", "section"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)

        # Document attributes
        self.title: str = ""
        self.language: Optional[str] = None
        self.canonical: Optional[str] = None
        self.canonicals: List[str] = []
        self.meta_tags: List[Dict[str, str]] = []
        self.meta_robots: List[str] = []

        # Content structures
        self.headings: List[Heading] = []
        self.raw_links: List[Tuple[str, str, Optional[str]]] = []  # (href, text, rel)
        self.jsonld_blocks: List[Tuple[str, str, int]] = []  # (json_text, location, block_index)
        self.semantic_landmarks: List[str] = []
        self.tables: List[TableData] = []
        self.code_blocks: List[str] = []
        self.images: List[Dict[str, str]] = []
        self.ctas: List[CTA] = []
        self.hreflangs: List[HreflangLink] = []
        self.feed_links: List[str] = []
        self.dates: Dict[str, Optional[str]] = {"published": None, "modified": None}
        self.authors: List[str] = []
        self._text_chunks: List[str] = []

        # State machines
        self._tag_stack: List[str] = []
        self._hidden_depth: int = 0
        self._hidden_tag_stack: List[str] = []
        self._current_location: str = "head"  # "head" or "body"
        self._in_title: bool = False
        self._title_chunks: List[str] = []

        self._in_heading: bool = False
        self._current_heading_level: int = 0
        self._heading_chunks: List[str] = []

        self._in_link: bool = False
        self._current_link_href: str = ""
        self._current_link_rel: Optional[str] = None
        self._current_link_class: str = ""
        self._link_text_chunks: List[str] = []

        self._in_button: bool = False
        self._button_text_chunks: List[str] = []
        self._button_href: str = ""
        self._button_tag: str = "button"

        self._in_jsonld: bool = False
        self._jsonld_chunks: List[str] = []
        self._jsonld_index: int = 0

        self._in_code: bool = False
        self._code_chunks: List[str] = []

        # Table state
        self._in_table: bool = False
        self._in_th: bool = False
        self._in_td: bool = False
        self._cell_chunks: List[str] = []
        self._current_table_headers: List[str] = []
        self._current_table_rows: List[List[str]] = []
        self._current_table_row: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        self._tag_stack.append(tag_lower)
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower == "head":
            self._current_location = "head"
        elif tag_lower == "body":
            self._current_location = "body"

        if tag_lower == "html" and "lang" in attr_dict:
            self.language = attr_dict["lang"]

        # Track landmarks
        if tag_lower in self.LANDMARK_TAGS and tag_lower not in self.semantic_landmarks:
            self.semantic_landmarks.append(tag_lower)

        # Check for hidden elements or cookie/consent banners to suppress noisy boilerplate
        style_val = attr_dict.get("style", "").lower().replace(" ", "")
        class_id_val = f"{attr_dict.get('class', '')} {attr_dict.get('id', '')}".lower()
        is_hidden_node = (
            "hidden" in attr_dict
            or attr_dict.get("aria-hidden", "").lower() == "true"
            or "display:none" in style_val
            or "visibility:hidden" in style_val
            or bool(re.search(r"\b(cookie|consent|onetrust|cc-banner|modal-hidden)\b", class_id_val))
        )
        if is_hidden_node:
            self._hidden_depth += 1
            self._hidden_tag_stack.append(tag_lower)

        # Meta tags
        if tag_lower == "meta":
            name = attr_dict.get("name") or attr_dict.get("property") or attr_dict.get("http-equiv") or ""
            content = attr_dict.get("content", "")
            if name or content:
                self.meta_tags.append({"name": name, "content": content})
            name_lower = name.lower()
            if name_lower in {"robots", "googlebot", "bingbot"}:
                directives = [d.strip().lower() for d in content.split(",") if d.strip()]
                self.meta_robots.extend(directives)
            elif name_lower in {"article:published_time", "pubdate", "datepublished", "date", "dc.date"}:
                if not self.dates["published"]:
                    self.dates["published"] = content
            elif name_lower in {"article:modified_time", "last-modified", "datemodified", "dc.date.modified"}:
                if not self.dates["modified"]:
                    self.dates["modified"] = content
            elif name_lower in {"author", "article:author", "dc.creator"}:
                if content and content not in self.authors:
                    self.authors.append(content)

        # Canonical link & alternate hreflangs / discovery feeds
        elif tag_lower == "link":
            rel = attr_dict.get("rel", "").lower().split()
            if "canonical" in rel:
                href = attr_dict.get("href", "").strip()
                if href:
                    self.canonicals.append(href)
                    if not self.canonical:
                        self.canonical = href
            if "alternate" in rel:
                hreflang = attr_dict.get("hreflang", "").strip()
                href = attr_dict.get("href", "").strip()
                if hreflang and href:
                    self.hreflangs.append(HreflangLink(lang=hreflang, href=href))
                type_val = attr_dict.get("type", "").lower()
                if any(x in type_val for x in ("rss", "atom", "xml")):
                    if href and href not in self.feed_links:
                        self.feed_links.append(href)

        # Title
        elif tag_lower == "title":
            self._in_title = True
            self._title_chunks = []

        # Headings
        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._in_heading = True
            self._current_heading_level = int(tag_lower[1])
            self._heading_chunks = []

        # Buttons and CTAs
        elif tag_lower == "button" or (tag_lower in ("div", "span") and attr_dict.get("role", "").lower() == "button"):
            self._in_button = True
            self._button_tag = tag_lower
            self._button_href = attr_dict.get("data-href") or attr_dict.get("href") or ""
            self._button_text_chunks = []

        elif tag_lower == "input":
            itype = attr_dict.get("type", "").lower()
            if itype in ("submit", "button"):
                val = (attr_dict.get("value") or attr_dict.get("aria-label") or "").strip()
                if val:
                    is_comm = bool(COMMERCIAL_CTA_REGEX.search(val))
                    self.ctas.append(CTA(text=val, href="", tag="input", is_commercial_cta=is_comm))

        # Hyperlinks
        elif tag_lower == "a":
            self._in_link = True
            self._current_link_href = attr_dict.get("href", "")
            self._current_link_rel = attr_dict.get("rel")
            self._current_link_class = attr_dict.get("class", "")
            self._link_text_chunks = []

        # Images
        elif tag_lower == "img":
            src = attr_dict.get("src", "")
            alt = attr_dict.get("alt", "")
            if src or alt:
                self.images.append({
                    "src": src,
                    "alt": alt,
                    "class": attr_dict.get("class", ""),
                    "id": attr_dict.get("id", ""),
                })
            if alt:
                if self._in_link:
                    self._link_text_chunks.append(alt)
                if self._in_button:
                    self._button_text_chunks.append(alt)

        # JSON-LD
        elif tag_lower == "script":
            script_type = attr_dict.get("type", "").lower()
            if script_type == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_chunks = []

        # Code
        elif tag_lower in {"pre", "code"}:
            self._in_code = True
            self._code_chunks = []

        # Tables
        elif tag_lower == "table":
            self._in_table = True
            self._current_table_headers = []
            self._current_table_rows = []
        elif tag_lower == "tr" and self._in_table:
            self._current_table_row = []
        elif tag_lower == "th" and self._in_table:
            self._in_th = True
            self._cell_chunks = []
        elif tag_lower == "td" and self._in_table:
            self._in_td = True
            self._cell_chunks = []

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if self._tag_stack and self._tag_stack[-1] == tag_lower:
            self._tag_stack.pop()

        if self._hidden_tag_stack and self._hidden_tag_stack[-1] == tag_lower:
            self._hidden_tag_stack.pop()
            self._hidden_depth = max(0, self._hidden_depth - 1)

        if tag_lower == "title":
            self._in_title = False
            self.title = " ".join(self._title_chunks).strip()

        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._in_heading:
            self._in_heading = False
            heading_text = " ".join(self._heading_chunks).strip()
            if heading_text and self._hidden_depth == 0:
                self.headings.append(
                    Heading(level=self._current_heading_level, text=heading_text)
                )

        elif tag_lower in ("button", "div", "span") and self._in_button:
            self._in_button = False
            btn_text = " ".join(self._button_text_chunks).strip()
            if btn_text:
                is_comm = bool(COMMERCIAL_CTA_REGEX.search(btn_text))
                self.ctas.append(
                    CTA(text=btn_text, href=self._button_href, tag=self._button_tag, is_commercial_cta=is_comm)
                )

        elif tag_lower == "a" and self._in_link:
            self._in_link = False
            link_text = " ".join(self._link_text_chunks).strip()
            if self._current_link_href:
                self.raw_links.append(
                    (self._current_link_href, link_text, self._current_link_rel)
                )
                is_btn = bool(re.search(r"\b(btn|button|cta|action)\b", self._current_link_class, re.I))
                is_comm = bool(COMMERCIAL_CTA_REGEX.search(link_text))
                if (is_comm or is_btn) and link_text:
                    self.ctas.append(
                        CTA(text=link_text, href=self._current_link_href, tag="a", is_commercial_cta=is_comm)
                    )

        elif tag_lower == "script" and self._in_jsonld:
            self._in_jsonld = False
            json_text = "".join(self._jsonld_chunks).strip()
            if json_text:
                self.jsonld_blocks.append(
                    (json_text, self._current_location, self._jsonld_index)
                )
                self._jsonld_index += 1

        elif tag_lower in {"pre", "code"} and self._in_code:
            self._in_code = False
            code_text = "".join(self._code_chunks).strip()
            if code_text and len(code_text) > 10:
                self.code_blocks.append(code_text)

        elif tag_lower == "th" and self._in_th:
            self._in_th = False
            cell_text = " ".join(self._cell_chunks).strip()
            self._current_table_headers.append(cell_text)

        elif tag_lower == "td" and self._in_td:
            self._in_td = False
            cell_text = " ".join(self._cell_chunks).strip()
            self._current_table_row.append(cell_text)

        elif tag_lower == "tr" and self._in_table:
            if self._current_table_row:
                self._current_table_rows.append(self._current_table_row)

        elif tag_lower == "table" and self._in_table:
            self._in_table = False
            if self._current_table_headers or self._current_table_rows:
                self.tables.append(
                    TableData(
                        headers=self._current_table_headers,
                        rows=self._current_table_rows,
                    )
                )

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_chunks.append(data)
        if self._in_heading:
            self._heading_chunks.append(data)
        if self._in_link:
            self._link_text_chunks.append(data)
        if self._in_button:
            self._button_text_chunks.append(data)
        if self._in_jsonld:
            self._jsonld_chunks.append(data)
        if self._in_code:
            self._code_chunks.append(data)
        if self._in_th or self._in_td:
            self._cell_chunks.append(data)

        # Append to general visible text stream if inside body, not title/code/table-cell, and not hidden
        if (
            self._current_location == "body"
            and not self._in_title
            and not self._in_code
            and not self._in_th
            and not self._in_td
            and self._hidden_depth == 0
            and not any(t in self.IGNORE_TAGS for t in self._tag_stack)
        ):
            self._text_chunks.append(data)

    def get_accumulated_text(self) -> str:
        """Returns normalized visible text content from the document."""
        raw_text = " ".join(self._text_chunks)
        # Collapse excessive whitespace
        return " ".join(raw_text.split())

    def parse_http_headers(self, headers: Dict[str, str]) -> List[str]:
        """Extracts X-Robots-Tag directives, Link canonicals, and modification dates from HTTP headers."""
        x_robots: List[str] = []
        if not headers:
            return x_robots
        for k, v in headers.items():
            k_lower = k.lower()
            if k_lower == "x-robots-tag":
                directives = [d.strip().lower() for d in v.split(",") if d.strip()]
                x_robots.extend(directives)
                self.meta_robots.extend(directives)
            elif k_lower == "link":
                m = re.search(r'<([^>]+)>;\s*rel=["\']?canonical["\']?', v, re.IGNORECASE)
                if m:
                    c_url = m.group(1).strip()
                    if c_url:
                        self.canonicals.append(c_url)
                        if not self.canonical:
                            self.canonical = c_url
            elif k_lower == "last-modified" and not self.dates["modified"]:
                self.dates["modified"] = v.strip()
        return x_robots
