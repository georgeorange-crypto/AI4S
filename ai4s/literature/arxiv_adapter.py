"""Bounded arXiv metadata adapter using the maintained arxiv.py API client."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

import arxiv  # type: ignore[import-untyped]

from .crossref import MAX_QUERY_LENGTH, MAX_RESULTS, PublicRateLimiter, RateLimiter


def approval_scope(query: str, max_results: int) -> str:
    normalized = " ".join(query.split())
    if not normalized or len(normalized) > MAX_QUERY_LENGTH:
        raise ValueError(f"query must contain 1-{MAX_QUERY_LENGTH} characters")
    if max_results < 1 or max_results > MAX_RESULTS:
        raise ValueError(f"max_results must be between 1 and {MAX_RESULTS}")
    query_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"arxiv-read:query-sha256:{query_hash}:max-results:{max_results}"


class ArxivAdapter:
    """Read-only metadata search; never downloads paper PDFs or source files."""

    def __init__(
        self,
        *,
        client: Any | None = None,
        limiter: RateLimiter | None = None,
        approval_consumer: Callable[[str, str], None] | None = None,
        timeout_seconds: float = 8.0,
    ):
        self.client = (
            client if client is not None else arxiv.Client(page_size=MAX_RESULTS, delay_seconds=0, num_retries=0)
        )
        session = getattr(self.client, "_session", None)
        if session is None or not hasattr(session, "hooks"):
            raise TypeError("arxiv.py client does not expose the pinned response-hook contract")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        original_request = session.request

        def bounded_request(method: str, url: str, **kwargs: Any) -> Any:
            kwargs.setdefault("timeout", timeout_seconds)
            return original_request(method, url, **kwargs)

        session.request = bounded_request
        self._responses: list[Any] = []
        session.hooks.setdefault("response", []).append(self._capture)
        self._limiter = limiter or PublicRateLimiter(interval_seconds=3.1)
        self._approval_consumer = approval_consumer

    def _capture(self, response: Any, *args: Any, **kwargs: Any) -> Any:
        self._responses.append(response)
        return response

    def search(self, query: str, max_results: int = 3, *, approval_id: str | None = None) -> dict[str, Any]:
        normalized = " ".join(query.split())
        scope = approval_scope(normalized, max_results)
        if not approval_id or self._approval_consumer is None:
            raise PermissionError("arXiv search requires a one-use approval consumer and exact approval ID")
        self._approval_consumer(approval_id, scope)
        self._responses.clear()
        slot = getattr(self._limiter, "slot", None)
        if callable(slot):
            with slot():
                records = self._search_records(normalized, max_results)
        else:
            self._limiter.wait()
            records = self._search_records(normalized, max_results)
        if len(records) > max_results:
            raise RuntimeError("arXiv client returned more records than requested")
        if len(self._responses) != 1:
            raise RuntimeError(f"expected exactly one captured arXiv response, got {len(self._responses)}")
        response = self._responses[0]
        raw = bytes(response.content)
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"arXiv returned HTTP {response.status_code}")
        return {
            "provider": "arxiv",
            "request_url": str(response.url),
            "request": {"operation": "search", "query": normalized, "max_results": max_results},
            "status_code": response.status_code,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "raw_response_text": raw.decode("utf-8"),
            "records": records,
            "license_status": "arXiv API metadata terms; metadata only",
        }

    def _search_records(self, query: str, max_results: int) -> list[dict[str, Any]]:
        search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
        return [self._record(result) for result in self.client.results(search)]

    @staticmethod
    def _record(result: Any) -> dict[str, Any]:
        return {
            "arxiv_id": result.get_short_id(),
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "doi": result.doi,
            "primary_category": result.primary_category,
            "categories": list(result.categories),
            "comment": result.comment,
            "journal_ref": result.journal_ref,
            "url": result.entry_id,
        }
