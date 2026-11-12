"""Bounded Crossref REST adapter. Abstract/full-text fields are deliberately excluded."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Protocol

BASE_URL = "https://api.crossref.org"
MAX_QUERY_LENGTH = 256
MAX_RESULTS = 5
MAX_RESPONSE_BYTES = 1_000_000
REQUEST_INTERVAL_SECONDS = 1.05
FIELDS = "DOI,title,author,published,publisher,type,URL,container-title,volume,issue,page,license"
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/[^\s<>\"#?]+$", re.IGNORECASE)


class CrossrefError(RuntimeError):
    """A bounded, non-retryable Crossref request or response error."""


class PublicRateLimiter:
    """Single-process, serial limiter for the stricter public Crossref pool."""

    def __init__(self, interval_seconds: float = REQUEST_INTERVAL_SECONDS) -> None:
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()
        self._last_request = 0.0

    def wait(self) -> None:
        with self._lock:
            delay = self.interval_seconds - (time.monotonic() - self._last_request)
            if delay > 0:
                time.sleep(delay)
            self._last_request = time.monotonic()


class SQLiteRateLimiter:
    """Persist request start spacing across CLI processes sharing the research DB."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        bucket: str = "crossref",
        interval_seconds: float = REQUEST_INTERVAL_SECONDS,
    ):
        self.connection = connection
        self.bucket = bucket
        self.interval_seconds = interval_seconds

    def wait(self) -> None:
        while True:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute(
                "SELECT last_started FROM network_rate_limits WHERE bucket=?", (self.bucket,)
            ).fetchone()
            now_seconds = time.time()
            delay = self.interval_seconds - (now_seconds - float(row[0])) if row else 0.0
            if delay <= 0:
                self.connection.execute(
                    "INSERT INTO network_rate_limits(bucket,last_started) VALUES(?,?) "
                    "ON CONFLICT(bucket) DO UPDATE SET last_started=excluded.last_started",
                    (self.bucket, now_seconds),
                )
                self.connection.commit()
                return
            self.connection.rollback()
            time.sleep(delay)

    @contextmanager
    def slot(self) -> Iterator[None]:
        """Hold SQLite's cross-process write lock for one spaced network request."""
        while True:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute(
                "SELECT last_started FROM network_rate_limits WHERE bucket=?", (self.bucket,)
            ).fetchone()
            now_seconds = time.time()
            delay = self.interval_seconds - (now_seconds - float(row[0])) if row else 0.0
            if delay <= 0:
                self.connection.execute(
                    "INSERT INTO network_rate_limits(bucket,last_started) VALUES(?,?) "
                    "ON CONFLICT(bucket) DO UPDATE SET last_started=excluded.last_started",
                    (self.bucket, now_seconds),
                )
                try:
                    yield
                finally:
                    self.connection.commit()
                return
            self.connection.rollback()
            time.sleep(delay)


_PUBLIC_LIMITER = PublicRateLimiter()
Transport = Callable[[str, float], tuple[int, Mapping[str, str], bytes]]


class RateLimiter(Protocol):
    def wait(self) -> None: ...


def normalize_query(query: str) -> str:
    normalized = " ".join(query.strip().split())
    if not normalized:
        raise ValueError("query must not be empty")
    if len(normalized) > MAX_QUERY_LENGTH:
        raise ValueError(f"query must be at most {MAX_QUERY_LENGTH} characters")
    return normalized


def normalize_doi(value: str) -> str:
    doi = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            doi = doi[len(prefix) :].strip()
            break
    if not DOI_PATTERN.fullmatch(doi):
        raise ValueError("invalid DOI syntax")
    return doi.lower()


def approval_scope(query: str, max_results: int) -> str:
    normalized = normalize_query(query)
    if max_results < 1 or max_results > MAX_RESULTS:
        raise ValueError(f"max_results must be between 1 and {MAX_RESULTS}")
    query_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"crossref-read:query-sha256:{query_hash}:max-results:{max_results}"


def doi_approval_scope(doi: str) -> str:
    normalized = normalize_doi(doi)
    doi_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"crossref-read:doi-sha256:{doi_hash}"


class CrossrefAdapter:
    """One read-only provider adapter; each method performs exactly one HTTP request."""

    def __init__(
        self,
        *,
        transport: Transport | None = None,
        limiter: RateLimiter | None = None,
        timeout_seconds: float = 8.0,
    ) -> None:
        self._transport = transport or self._request
        self._limiter = limiter or _PUBLIC_LIMITER
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _request(url: str, timeout_seconds: float) -> tuple[int, Mapping[str, str], bytes]:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "AI4S-ResearchOS/0.2 (read-only scholarly metadata integration)",
            },
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
                return response.status, dict(response.headers.items()), body
        except urllib.error.HTTPError as exc:
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            raise CrossrefError(
                f"Crossref returned HTTP {exc.code}; retry-after={retry_after or 'unspecified'}"
            ) from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise CrossrefError(f"Crossref request failed: {type(exc).__name__}") from None

    def _get(self, url: str, request: dict[str, Any]) -> dict[str, Any]:
        self._limiter.wait()
        status_code, headers, body = self._transport(url, self.timeout_seconds)
        if status_code < 200 or status_code >= 300:
            retry_after = headers.get("Retry-After") or headers.get("retry-after") or "unspecified"
            raise CrossrefError(f"Crossref returned HTTP {status_code}; retry-after={retry_after}")
        if len(body) > MAX_RESPONSE_BYTES:
            raise CrossrefError(f"Crossref response exceeded {MAX_RESPONSE_BYTES} bytes")
        try:
            parsed = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise CrossrefError("Crossref returned invalid JSON") from None
        if parsed.get("status") != "ok" or not isinstance(parsed.get("message"), dict):
            raise CrossrefError("Crossref response did not contain an OK message")
        selected_headers = {
            key.lower(): value
            for key, value in headers.items()
            if key.lower()
            in {"date", "x-rate-limit-limit", "x-rate-limit-interval", "x-rate-limit-type", "x-concurrency-limit"}
        }
        return {
            "provider": "crossref",
            "request_url": url,
            "request": request,
            "status_code": status_code,
            "response_headers": selected_headers,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "raw_response_text": body.decode("utf-8"),
            "response_json": parsed,
        }

    def search(self, query: str, max_results: int = 3) -> dict[str, Any]:
        normalized = normalize_query(query)
        if max_results < 1 or max_results > MAX_RESULTS:
            raise ValueError(f"max_results must be between 1 and {MAX_RESULTS}")
        parameters = urllib.parse.urlencode({"query.title": normalized, "rows": max_results, "select": FIELDS})
        url = f"{BASE_URL}/works?{parameters}"
        envelope = self._get(url, {"operation": "search", "query": normalized, "max_results": max_results})
        items = envelope["response_json"]["message"].get("items", [])
        if not isinstance(items, list) or len(items) > max_results:
            raise CrossrefError("Crossref search returned an invalid result list")
        envelope["records"] = [normalize_record(item) for item in items]
        return envelope

    def resolve(self, doi: str) -> dict[str, Any]:
        normalized = normalize_doi(doi)
        # The single-work route rejects `select`; filter the DOI through /works instead so
        # the raw response never contains publisher-owned abstracts.
        parameters = urllib.parse.urlencode({"filter": f"doi:{normalized}", "rows": 1, "select": FIELDS})
        url = f"{BASE_URL}/works?{parameters}"
        envelope = self._get(url, {"operation": "resolve", "doi": normalized})
        items = envelope["response_json"]["message"].get("items", [])
        if not isinstance(items, list) or len(items) > 1:
            raise CrossrefError("Crossref DOI filter returned an invalid result list")
        envelope["record"] = normalize_record(items[0]) if items else None
        return envelope


def normalize_record(item: Mapping[str, Any]) -> dict[str, Any]:
    titles = item.get("title") or []
    authors = item.get("author") or []
    published = item.get("published") or item.get("issued") or {}
    date_parts = published.get("date-parts") or []
    year = date_parts[0][0] if date_parts and date_parts[0] else None
    return {
        "doi": item.get("DOI"),
        "title": titles[0] if titles else None,
        "authors": [" ".join(part for part in (a.get("given"), a.get("family")) if part) for a in authors],
        "year": year,
        "publisher": item.get("publisher"),
        "type": item.get("type"),
        "url": item.get("URL"),
        "container_title": (item.get("container-title") or [None])[0],
        "volume": item.get("volume"),
        "issue": item.get("issue"),
        "page": item.get("page"),
        "license_urls": [entry.get("URL") for entry in item.get("license", []) if entry.get("URL")],
    }


def normalize_title(title: str | None) -> str:
    return " ".join(re.findall(r"[\w]+", (title or "").casefold()))
