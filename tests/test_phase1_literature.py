import hashlib
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from ai4s.agents.literature_graph import run_literature_graph
from ai4s.core import ResearchStore
from ai4s.literature.crossref import (
    CrossrefAdapter,
    CrossrefError,
    PublicRateLimiter,
    SQLiteRateLimiter,
    approval_scope,
    doi_approval_scope,
)
from ai4s.skills.registry import SkillRegistry, SkillValidationError, skill_approval_scope

ROOT = Path(__file__).resolve().parents[1]
QUERY = "A reproducible test paper"
RECORD = {
    "DOI": "10.5555/example.1",
    "title": [QUERY],
    "author": [{"given": "Ada", "family": "Lovelace"}],
    "published": {"date-parts": [[2024]]},
    "publisher": "Example Society",
    "type": "journal-article",
    "URL": "https://doi.org/10.5555/example.1",
    "container-title": ["Example Journal"],
}


def response(message):
    return json.dumps({"status": "ok", "message": message}, separators=(",", ":")).encode()


class FakeTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        message = {"items": [RECORD]} if "/works?" in url else RECORD
        return 200, {"X-Rate-Limit-Limit": "1"}, response(message)


class FailOnceOnResolveTransport(FakeTransport):
    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        if len(self.calls) == 2:
            return 503, {"Retry-After": "2"}, b"temporary upstream failure"
        message = {"items": [RECORD]} if "/works?" in url else RECORD
        return 200, {}, response(message)


class Phase1LiteratureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = ResearchStore(self.root / "research.sqlite")
        self.skill = SkillRegistry(ROOT / "skills").load("literature-evidence-review")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def _approvals(self):
        network = self.store.approve("network_tool", "test-human", approval_scope(QUERY, 2))
        skill = self.store.approve("skill_activation", "test-human", skill_approval_scope(self.skill))
        return network, skill

    def test_crossref_adapter_bounds_query_results_and_preserves_raw_checksum(self):
        transport = FakeTransport()
        adapter = CrossrefAdapter(transport=transport, limiter=PublicRateLimiter(0))
        result = adapter.search(QUERY, 2)
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(result["records"][0]["doi"], RECORD["DOI"])
        self.assertEqual(hashlib.sha256(result["raw_response_text"].encode()).hexdigest(), result["response_sha256"])
        self.assertNotIn("abstract", result["request_url"].lower())
        with self.assertRaises(ValueError):
            adapter.search(QUERY, 6)
        with self.assertRaises(ValueError):
            adapter.resolve("javascript:alert(1)")

    def test_crossref_rejects_large_and_invalid_responses(self):
        too_large = CrossrefAdapter(
            transport=lambda _url, _timeout: (200, {}, b"x" * 1_000_001), limiter=PublicRateLimiter(0)
        )
        with self.assertRaises(CrossrefError):
            too_large.search(QUERY)
        invalid = CrossrefAdapter(transport=lambda _url, _timeout: (200, {}, b"not-json"), limiter=PublicRateLimiter(0))
        with self.assertRaises(CrossrefError):
            invalid.search(QUERY)

    def test_sqlite_rate_limiter_persists_request_spacing(self):
        limiter_a = SQLiteRateLimiter(self.store.db, interval_seconds=0.04)
        limiter_b = SQLiteRateLimiter(self.store.db, interval_seconds=0.04)
        limiter_a.wait()
        started = time.monotonic()
        limiter_b.wait()
        self.assertGreaterEqual(time.monotonic() - started, 0.025)

    def test_skill_registry_rejects_unreviewed_tools_and_yaml_tags(self):
        unsafe = self.root / "skills"
        skill_dir = unsafe / "bad-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: bad-skill\ndescription: test\nallowed-tools: host_shell\n---\nrun it", encoding="utf-8"
        )
        with self.assertRaises(SkillValidationError):
            SkillRegistry(unsafe).load("bad-skill")

        (skill_dir / "SKILL.md").write_text(
            "---\n!!python/object/apply:os.system ['echo pwned']\n---\ninert", encoding="utf-8"
        )
        with self.assertRaises(SkillValidationError):
            SkillRegistry(unsafe).load("bad-skill")

    def test_cli_help_does_not_import_optional_agent_runtime(self):
        script = "import builtins,sys\noriginal=builtins.__import__\ndef guarded(name,*args,**kwargs):\n if name.split('.')[0] in {'mcp','langgraph','langchain_core','yaml'}: raise AssertionError('optional Phase 1 runtime imported')\n return original(name,*args,**kwargs)\nbuiltins.__import__=guarded\nfrom ai4s.cli import main\nsys.argv=['ai4s','--help']\ntry:\n main()\nexcept SystemExit as exc:\n raise SystemExit(0 if exc.code == 0 else exc.code)\n"
        process = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIn("run-offline", process.stdout)

    def test_mcp_langgraph_persists_checkpoints_artifacts_and_consumes_approvals(self):
        network, skill = self._approvals()
        transport = FakeTransport()
        adapter = CrossrefAdapter(transport=transport, limiter=PublicRateLimiter(0))
        args = dict(
            store=self.store,
            query=QUERY,
            max_results=2,
            run_key="phase1-test",
            output_root=self.root / "artifacts",
            checkpoints_path=self.root / "checkpoints.sqlite",
            crossref_approval_id=network,
            skill_approval_id=skill,
            skill_root=ROOT / "skills",
            adapter=adapter,
        )
        result = run_literature_graph(**args)
        self.assertEqual(result["status"], "identity_match")
        self.assertIsNone(result["model_used"])
        self.assertEqual(len(transport.calls), 2)
        self.assertTrue((self.root / "checkpoints.sqlite").exists())
        checkpoint_db = __import__("sqlite3").connect(self.root / "checkpoints.sqlite")
        try:
            self.assertGreater(checkpoint_db.execute("SELECT COUNT(*) FROM checkpoints").fetchone()[0], 0)
        finally:
            checkpoint_db.close()
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM literature_tool_calls").fetchone()[0], 2)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM literature_evidence").fetchone()[0], 1)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0], 2)
        self.assertIsNotNone(
            self.store.db.execute("SELECT used_at FROM approvals WHERE id=?", (network,)).fetchone()["used_at"]
        )
        again = run_literature_graph(**args)
        self.assertEqual(again, result)
        self.assertEqual(len(transport.calls), 2)

    def test_graph_denies_wrong_scope_before_network(self):
        network = self.store.approve("network_tool", "test-human", approval_scope("some other query", 2))
        skill = self.store.approve("skill_activation", "test-human", skill_approval_scope(self.skill))
        transport = FakeTransport()
        with self.assertRaises(PermissionError):
            run_literature_graph(
                self.store,
                query=QUERY,
                max_results=2,
                run_key="denied",
                output_root=self.root / "out",
                checkpoints_path=self.root / "cp.sqlite",
                crossref_approval_id=network,
                skill_approval_id=skill,
                skill_root=ROOT / "skills",
                adapter=CrossrefAdapter(transport=transport, limiter=PublicRateLimiter(0)),
            )
        self.assertEqual(transport.calls, [])

    def test_direct_doi_lookup_uses_only_exact_doi_approval(self):
        doi = RECORD["DOI"]
        network = self.store.approve("network_tool", "test-human", doi_approval_scope(doi))
        skill = self.store.approve("skill_activation", "test-human", skill_approval_scope(self.skill))
        transport = FakeTransport()
        result = run_literature_graph(
            self.store,
            query="",
            max_results=1,
            run_key="direct-doi",
            output_root=self.root / "direct-artifacts",
            checkpoints_path=self.root / "direct-checkpoints.sqlite",
            crossref_approval_id=network,
            skill_approval_id=skill,
            skill_root=ROOT / "skills",
            adapter=CrossrefAdapter(transport=transport, limiter=PublicRateLimiter(0)),
            direct_doi=doi,
        )
        self.assertEqual(result["status"], "doi_resolved_title_uncompared")
        self.assertEqual(result["tools"], ["crossref_resolve"])
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(result["resolution"]["record"]["doi"], doi)

    def test_checkpoint_resume_after_tool_failure_skips_completed_search(self):
        network, skill = self._approvals()
        first_transport = FailOnceOnResolveTransport()
        base = dict(
            store=self.store,
            query=QUERY,
            max_results=2,
            run_key="resume-after-resolve-error",
            output_root=self.root / "resume-artifacts",
            checkpoints_path=self.root / "resume-checkpoints.sqlite",
            crossref_approval_id=network,
            skill_approval_id=skill,
            skill_root=ROOT / "skills",
        )
        with self.assertRaises(RuntimeError):
            run_literature_graph(
                **base,
                adapter=CrossrefAdapter(transport=first_transport, limiter=PublicRateLimiter(0)),
            )
        self.assertEqual(len(first_transport.calls), 2)
        second_transport = FakeTransport()
        recovered = run_literature_graph(
            **base,
            adapter=CrossrefAdapter(transport=second_transport, limiter=PublicRateLimiter(0)),
        )
        self.assertEqual(recovered["status"], "identity_match")
        self.assertEqual(len(second_transport.calls), 1)
        self.assertIn("/works?filter=doi%3A", second_transport.calls[0][0])


if __name__ == "__main__":
    unittest.main()
