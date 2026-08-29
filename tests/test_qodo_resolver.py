"""Unit tests for Qodo PR Self-Healing Integration (qodo-pr-resolver)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cortex_vector_mcp.store import Store
from sandbox.qodo.qodo_resolver import (
    QodoFinding,
    check_architectural_veto,
    format_inline_reply,
    format_summary_comment,
    resolve_qodo_findings,
)


class TestQodoResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = Store(persist_dir=Path(self.temp_dir.name))

        # Seed active ADR-002 enforcing Redis for session persistence
        self.adr2 = {
            "id": "ADR-002",
            "title": "Redis for Distributed Session Persistence",
            "author": "senior-dev",
            "date": "2026-05-15",
            "status": "ACTIVE",
            "merged_pr": 89,
            "reasoning": "Pod resilience and sub-2ms response latency.",
            "invariants": ["Session state MUST never be stored in process memory. They MUST be stored in the shared Redis cache layer."],
            "scope_files": ["src/cache/session.py"],
        }
        self.store.upsert_decision(self.adr2)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_architectural_veto_declines_redis_to_dict_fix(self) -> None:
        finding = QodoFinding(
            id="1998877701",
            thread_id="thread_1",
            severity="WARNING",
            file="src/cache/session.py",
            line=12,
            title="In-memory cache optimization",
            suggestion="Replace Redis network call with an in-process local map for faster session access.",
        )

        declined, adr, confidence, explanation = check_architectural_veto(finding, self.store)
        self.assertTrue(declined)
        self.assertIsNotNone(adr)
        self.assertEqual(adr.id, "ADR-002")
        self.assertGreaterEqual(confidence, 80.0)
        self.assertIn("in-process memory", explanation)

    def test_resolve_qodo_findings_output_contract(self) -> None:
        raw_findings = [
            {
                "id": "101",
                "severity": "ERROR",
                "file": "src/api/handlers.py",
                "title": "Missing HTTP timeout",
                "suggestion": "Add explicit 5s timeout to outbound fetch call.",
            },
            {
                "id": "102",
                "severity": "WARNING",
                "file": "src/cache/session.py",
                "title": "Redis latency",
                "suggestion": "Use local in-memory dict instead of Redis roundtrip.",
            },
            {
                "id": "103",
                "severity": "RECOMMENDATION",
                "file": "src/utils.py",
                "title": "Docstring formatting",
                "suggestion": "Reformat docstring.",
            },
        ]

        res = resolve_qodo_findings(pr=142, findings=raw_findings, store=self.store)

        self.assertEqual(res["pr"], 142)
        self.assertEqual(len(res["findings"]), 3)

        # 101 -> fixed
        f101 = next(f for f in res["findings"] if f["id"] == "101")
        self.assertEqual(f101["action"], "fixed")

        # 102 -> declined-architectural
        f102 = next(f for f in res["findings"] if f["id"] == "102")
        self.assertEqual(f102["action"], "declined-architectural")
        self.assertEqual(f102["adr_id"], "ADR-002")

        # 103 -> skipped
        f103 = next(f for f in res["findings"] if f["id"] == "103")
        self.assertEqual(f103["action"], "skipped")
        self.assertEqual(f103["reason"], "recommendation-deferred")

    def test_format_inline_reply_templates(self) -> None:
        finding = QodoFinding(
            id="102",
            thread_id="thread_1",
            severity="WARNING",
            file="src/cache/session.py",
            line=12,
            title="Redis latency",
            suggestion="Use local dict.",
        )
        reply = format_inline_reply(
            finding,
            action="declined-architectural",
            adr=self.store.get_decision("ADR-002"),
            confidence=95.0,
            conflict_explanation="Violates session persistence invariant.",
        )

        self.assertIn("<!-- codebase-cortex:qodo-fix:102 -->", reply)
        self.assertIn("Fix Declined: Architectural Invariant", reply)
        self.assertIn("ADR-002", reply)
        self.assertIn("@senior-dev", reply)


if __name__ == "__main__":
    unittest.main()
