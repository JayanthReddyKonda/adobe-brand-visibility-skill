"""Global audit budget enforcing hard ceilings on time, pages, bytes, and concurrency.

Guarantees that no subsystem can escape the global audit deadline or consume excessive resources.
Pure Python standard library (threading.Lock, time.monotonic).
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict


class BudgetExhaustedError(RuntimeError):
    """Raised when an operation would exceed the allocated audit budget."""


class Budget:
    """Enforces resource limits and monotonic deadlines across crawler components."""

    def __init__(
        self,
        time_limit_sec: float = 180.0,
        max_pages: int = 28,
        max_total_bytes: int = 50 * 1024 * 1024,
        max_page_bytes: int = 2500000,
        max_depth: int = 3,
        max_redirects: int = 5,
        max_concurrency: int = 8,
    ) -> None:
        self.time_limit_sec = float(time_limit_sec)
        self.max_pages = int(max_pages)
        self.max_total_bytes = int(max_total_bytes)
        self.max_page_bytes = int(max_page_bytes)
        self.max_depth = int(max_depth)
        self.max_redirects = int(max_redirects)
        self.max_concurrency = int(max_concurrency)

        self._start_time = time.monotonic()
        self._deadline = self._start_time + self.time_limit_sec
        self._requests_made = 0
        self._pages_fetched = 0
        self._pages_reserved = 0
        self._bytes_downloaded = 0
        self._lock = threading.RLock()

    def remaining_time(self) -> float:
        """Returns the number of seconds remaining before the deadline (minimum 0.0)."""
        rem = self._deadline - time.monotonic()
        return max(0.0, rem)

    def elapsed_time(self) -> float:
        """Returns the total elapsed seconds since budget inception."""
        return time.monotonic() - self._start_time

    def is_exhausted(self) -> bool:
        """Checks whether time, page count, or byte budget has been exhausted."""
        with self._lock:
            return (
                time.monotonic() >= self._deadline
                or self._pages_fetched >= self.max_pages
                or self._bytes_downloaded >= self.max_total_bytes
            )

    def can_fetch_page(self, depth: int = 0) -> bool:
        """Determines if another page can be fetched within depth and resource constraints."""
        if depth > self.max_depth:
            return False
        with self._lock:
            return (
                time.monotonic() < self._deadline
                and (self._pages_fetched + self._pages_reserved) < self.max_pages
                and self._bytes_downloaded < self.max_total_bytes
            )

    def reserve_page_slot(self, depth: int = 0) -> bool:
        """Atomically reserves a page slot for an in-flight worker task."""
        if depth > self.max_depth:
            return False
        with self._lock:
            if (
                time.monotonic() < self._deadline
                and (self._pages_fetched + self._pages_reserved) < self.max_pages
                and self._bytes_downloaded < self.max_total_bytes
            ):
                self._pages_reserved += 1
                return True
            return False

    def commit_page_slot(self) -> None:
        """Atomically commits a successfully fetched HTML page, decrementing reservation."""
        with self._lock:
            if self._pages_reserved > 0:
                self._pages_reserved -= 1
            self._pages_fetched += 1

    def release_page_slot(self) -> None:
        """Atomically releases a reserved page slot on fetch failure or non-HTML resource."""
        with self._lock:
            if self._pages_reserved > 0:
                self._pages_reserved -= 1

    def record_request(self) -> None:
        """Thread-safely records an HTTP request attempt (infrastructure or page)."""
        with self._lock:
            self._requests_made += 1

    def record_page(self) -> None:
        """Thread-safely records a completed HTML content page fetch."""
        with self._lock:
            self._pages_fetched += 1

    def record_bytes(self, count: int) -> None:
        """Thread-safely records bytes received."""
        with self._lock:
            self._bytes_downloaded += max(0, count)

    def check_or_raise(self) -> None:
        """Raises BudgetExhaustedError if the budget is exhausted."""
        if self.is_exhausted():
            raise BudgetExhaustedError(
                f"Audit budget exhausted: elapsed={self.elapsed_time():.1f}s, "
                f"pages={self._pages_fetched}/{self.max_pages}, "
                f"bytes={self._bytes_downloaded}/{self.max_total_bytes}"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Returns current resource utilization metrics."""
        with self._lock:
            return {
                "elapsed_sec": round(self.elapsed_time(), 2),
                "remaining_sec": round(self.remaining_time(), 2),
                "requests_made": self._requests_made,
                "pages_fetched": self._pages_fetched,
                "max_pages": self.max_pages,
                "bytes_downloaded": self._bytes_downloaded,
                "max_total_bytes": self.max_total_bytes,
                "is_exhausted": self.is_exhausted(),
            }
