"""Single-pass streaming HTML parser for multi-signal page extraction.

Collects metadata, headings (H1-H6), hyperlinks, tables, code blocks,
semantic landmark tags, and JSON-LD script bodies without building a heavy DOM tree.
Pure Python standard library (html.parser.HTMLParser).
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

from .models import Heading, TableData


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
        self.meta_tags: List[Dict[str, str]] = []
        self.meta_robots: List[str] = []

        # Content structures
        self.headings: List[Heading] = []
        self.raw_links: List[Tuple[str, str, Optional[str]]] = []  # (href, text, rel)
        self.jsonld_blocks: List[Tuple[str, str, int]] = []  # (json_text, location, block_index)
        self.semantic_landmarks: List[str] = []
        self.tables: List[TableData] = []
        self.code_blocks: List[str] = []

        # State machines
        self._tag_stack: List[str] = []
        self._current_location: str = "head"  # "head" or "body"
        self._in_title: bool = False
        self._title_chunks: List[str] = []

        self._in_heading: bool = False
        self._current_heading_level: int = 0
        self._heading_chunks: List[str] = []

        self._in_link: bool = False
        self._current_link_href: str = ""
        self._current_link_rel: Optional[str] = None
        self._link_text_chunks: List[str] = []

        self._in_jsonld: bool = False
        self._jsonld_chunks: List[str] = []
        self._jsonld_index: int = 0

        self._in_code: bool = False
        self._code_chunks: List[str] = []

        # Table state
        self._in_table: bool = False
        self._current_table_headers: List[str] = []
        self._current_table_rows: List[List[str]] = []
        self._current_table_row: List[str] = []
        self._in_th: bool = False
        self._in_td: bool = False
        self._cell_chunks: List[str] = []

        # Text stream
        self._text_chunks: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        tag_lower = tag.lower()
        self._tag_stack.append(tag_lower)
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        if tag_lower == "body":
            self._current_location = "body"

        if tag_lower == "html" and "lang" in attr_dict:
            self.language = attr_dict["lang"]

        # Track landmarks
        if tag_lower in self.LANDMARK_TAGS and tag_lower not in self.semantic_landmarks:
            self.semantic_landmarks.append(tag_lower)

        # Meta tags
        if tag_lower == "meta":
            name = attr_dict.get("name") or attr_dict.get("property") or attr_dict.get("http-equiv") or ""
            content = attr_dict.get("content", "")
            if name or content:
                self.meta_tags.append({"name": name, "content": content})
            if name.lower() in {"robots", "googlebot", "bingbot"}:
                directives = [d.strip().lower() for d in content.split(",") if d.strip()]
                self.meta_robots.extend(directives)

        # Canonical link
        elif tag_lower == "link":
            rel = attr_dict.get("rel", "").lower()
            if "canonical" in rel.split():
                href = attr_dict.get("href", "")
                if href:
                    self.canonical = href

        # Title
        elif tag_lower == "title":
            self._in_title = True
            self._title_chunks = []

        # Headings
        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._in_heading = True
            self._current_heading_level = int(tag_lower[1])
            self._heading_chunks = []

        # Hyperlinks
        elif tag_lower == "a":
            self._in_link = True
            self._current_link_href = attr_dict.get("href", "")
            self._current_link_rel = attr_dict.get("rel")
            self._link_text_chunks = []

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

        if tag_lower == "title":
            self._in_title = False
            self.title = " ".join(self._title_chunks).strip()

        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._in_heading:
            self._in_heading = False
            heading_text = " ".join(self._heading_chunks).strip()
            if heading_text:
                self.headings.append(
                    Heading(level=self._current_heading_level, text=heading_text)
                )

        elif tag_lower == "a" and self._in_link:
            self._in_link = False
            link_text = " ".join(self._link_text_chunks).strip()
            if self._current_link_href:
                self.raw_links.append(
                    (self._current_link_href, link_text, self._current_link_rel)
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
        if self._in_jsonld:
            self._jsonld_chunks.append(data)
        if self._in_code:
            self._code_chunks.append(data)
        if self._in_th or self._in_td:
            self._cell_chunks.append(data)

        # Append to general visible text stream if not inside ignore tags
        if not any(t in self.IGNORE_TAGS for t in self._tag_stack):
            self._text_chunks.append(data)

    def get_accumulated_text(self) -> str:
        """Returns normalized visible text content from the document."""
        raw_text = " ".join(self._text_chunks)
        # Collapse excessive whitespace
        return " ".join(raw_text.split())
