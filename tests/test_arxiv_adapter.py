import hashlib
import sqlite3
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from ai4s.cli import main
from ai4s.core import ResearchStore
from ai4s.literature.arxiv_adapter import ArxivAdapter, approval_scope
from ai4s.literature.crossref import PublicRateLimiter, SQLiteRateLimiter


class FakeSession:
    def __init__(self):
        self.hooks: dict[str, list] = {"response": []}
        self.last_request = None

    def request(self, method, url, **kwargs):
        self.last_request = (method, url, kwargs)
        return self.last_request


class FakeClient:
    def __init__(self):
        self._session = FakeSession()
        self.calls = 0

    def results(self, search):
        self.calls += 1
        raw = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2401.12345v2</id></entry></feed>'
        response = SimpleNamespace(
            content=raw, status_code=200, url="https://export.arxiv.org/api/query?search_query=all%3Agraph"
        )
        for hook in self._session.hooks["response"]:
            hook(response)
        assert search.max_results == 2
        yield SimpleNamespace(
            get_short_id=lambda: "2401.12345v2",
            title="A graph workflow",
            authors=[SimpleNamespace(name="Ada Researcher")],
            published=datetime(2024, 1, 1, tzinfo=timezone.utc),
            updated=datetime(2024, 2, 1, tzinfo=timezone.utc),
            doi="10.1234/example",
            primary_category="cs.AI",
            categories=["cs.AI", "cs.CL"],
            comment=None,
            journal_ref=None,
            entry_id="https://arxiv.org/abs/2401.12345v2",
        )


def test_arxiv_pinned_client_contract_and_raw_feed_provenance():
    consumed = []
    client = FakeClient()
    adapter = ArxivAdapter(
        client=client,
        limiter=PublicRateLimiter(0),
        approval_consumer=lambda approval, scope: consumed.append((approval, scope)),
    )
    client._session.request("GET", "https://fixture.invalid")
    assert client._session.last_request[2]["timeout"] == 8.0
    envelope = adapter.search("  all:graph   ", max_results=2, approval_id="approved-once")
    assert envelope["provider"] == "arxiv"
    assert envelope["request"]["query"] == "all:graph"
    assert envelope["response_sha256"] == hashlib.sha256(envelope["raw_response_text"].encode()).hexdigest()
    assert envelope["records"][0]["arxiv_id"] == "2401.12345v2"
    assert "abstract" not in envelope["records"][0]
    assert consumed == [("approved-once", approval_scope("all:graph", 2))]


@pytest.mark.parametrize("query,limit", [("", 1), ("valid", 6)])
def test_arxiv_bounds_fail_before_egress(query: str, limit: int):
    adapter = ArxivAdapter(
        client=FakeClient(), limiter=PublicRateLimiter(0), approval_consumer=lambda _approval, _scope: None
    )
    with pytest.raises(ValueError):
        adapter.search(query, max_results=limit, approval_id="test")


def test_arxiv_network_is_closed_without_persisted_approval_consumer():
    adapter = ArxivAdapter(client=FakeClient(), limiter=PublicRateLimiter(0))
    with pytest.raises(PermissionError):
        adapter.search("all:graph", approval_id="not-enough")


def test_arxiv_stored_approval_is_exact_and_one_use(tmp_path):
    store = ResearchStore(tmp_path / "research.sqlite")
    try:
        query = "all:graph"
        approval_id = store.approve("network_tool", "test-human", approval_scope(query, 2))

        def consume(approval: str, scope: str) -> None:
            store.consume_approvals([(approval, "network_tool", scope)])

        client = FakeClient()
        adapter = ArxivAdapter(
            client=client, limiter=SQLiteRateLimiter(store.db, "arxiv-test", 0), approval_consumer=consume
        )
        with pytest.raises(PermissionError):
            adapter.search("all:different", 2, approval_id=approval_id)
        assert client.calls == 0
        adapter.search(query, 2, approval_id=approval_id)
        with pytest.raises(PermissionError):
            adapter.search(query, 2, approval_id=approval_id)
        assert client.calls == 1
        used_at = store.db.execute("SELECT used_at FROM approvals WHERE id=?", (approval_id,)).fetchone()[0]
        assert used_at
    finally:
        store.close()


def test_arxiv_cli_records_denied_approval_without_network(monkeypatch, tmp_path):
    database = tmp_path / "research.sqlite"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "ai4s",
            "search-arxiv",
            "--db",
            str(database),
            "--query",
            "all:graph",
            "--approval-id",
            "missing-approval",
        ],
    )
    with pytest.raises(PermissionError):
        main()
    store = ResearchStore(database)
    try:
        row = store.db.execute(
            "SELECT event_type,payload FROM literature_events WHERE run_key='arxiv:missing-approval'"
        ).fetchone()
        assert row["event_type"] == "arxiv_search_failed"
        assert '"error_type": "PermissionError"' in row["payload"]
    finally:
        store.close()


def test_shared_sqlite_slot_blocks_a_second_provider_connection(tmp_path):
    database = tmp_path / "research.sqlite"
    store = ResearchStore(database)
    other_process_connection = sqlite3.connect(database, timeout=0)
    try:
        limiter = SQLiteRateLimiter(store.db, "arxiv-serialization-test", 0)
        with limiter.slot():
            with pytest.raises(sqlite3.OperationalError, match="locked"):
                other_process_connection.execute("BEGIN IMMEDIATE")
        other_process_connection.execute("BEGIN IMMEDIATE")
        other_process_connection.rollback()
    finally:
        other_process_connection.close()
        store.close()
