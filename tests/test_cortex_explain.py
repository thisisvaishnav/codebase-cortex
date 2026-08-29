"""Unit tests for cortex-explain multi-hop lineage reasoning and Q&A engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cortex_vector_mcp.explain import explain_query, format_explain_response, trace_adr_lineage
from cortex_vector_mcp.schema import ADR
from cortex_vector_mcp.store import Store


class TestCortexExplain(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = Store(persist_dir=Path(self.temp_dir.name))

        # Seed ADR-002 (SUPERSEDED) and ADR-005 (ACTIVE)
        self.adr2_payload = {
            "id": "ADR-002",
            "title": "Redis for Distributed Session Persistence",
            "author": "senior-dev",
            "date": "2026-05-15",
            "status": "SUPERSEDED",
            "superseded_by_adr": "ADR-005",
            "superseded_by_pr": 134,
            "merged_pr": 89,
            "reasoning": "Pod resilience in K8s and sub-2ms response latency.",
            "invariants": ["Session state MUST be stored in Redis."],
            "alternatives": ["Postgres session tables", "In-process local map"],
            "scope_files": ["src/cache/session.py"],
        }
        self.adr5_payload = {
            "id": "ADR-005",
            "title": "Encrypted Cookie Sessions for Zero-State Autoscale",
            "author": "lead-maintainer",
            "date": "2026-08-10",
            "status": "ACTIVE",
            "merged_pr": 134,
            "reasoning": "Eliminate Redis cluster dependency for session state to simplify deployment.",
            "invariants": ["Session tokens MUST be encrypted and signed in HTTP-only cookies."],
            "alternatives": ["Redis Cluster"],
            "scope_files": ["src/cache/session.py"],
        }

        self.store.upsert_decision(self.adr2_payload)
        self.store.upsert_decision(self.adr5_payload)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_trace_lineage_forward_and_backward(self) -> None:
        # Trace from ADR-002 should walk forward to ADR-005
        lineage = trace_adr_lineage(self.store, "ADR-002")
        self.assertEqual(len(lineage), 2)
        self.assertEqual(lineage[0].id, "ADR-002")
        self.assertEqual(lineage[1].id, "ADR-005")

        # Trace from ADR-005 should walk backward to find predecessor ADR-002
        lineage_from_5 = trace_adr_lineage(self.store, "ADR-005")
        self.assertEqual(len(lineage_from_5), 2)
        self.assertEqual(lineage_from_5[0].id, "ADR-002")
        self.assertEqual(lineage_from_5[1].id, "ADR-005")

    def test_explain_query_with_lineage(self) -> None:
        res = explain_query(self.store, query="Why did we choose Redis over Postgres?")
        self.assertIn("answer", res)
        self.assertIn("lineage", res)
        self.assertGreaterEqual(len(res["lineage"]), 1)

        answer_text = res["answer"]
        self.assertIn("ADR-002", answer_text)
        self.assertIn("@senior-dev", answer_text)
        self.assertIn("2026-05-15", answer_text)
        self.assertIn("SUPERSEDED", answer_text)
        self.assertIn("ADR-005", answer_text)
        self.assertIn("@lead-maintainer", answer_text)
        self.assertIn("Encrypted Cookie Sessions", answer_text)

    def test_explain_query_no_match(self) -> None:
        res = explain_query(self.store, query="Quantum Encryption Security Protocol")
        self.assertIn("Decision Not Found", res["answer"])
        self.assertEqual(len(res["lineage"]), 0)


if __name__ == "__main__":
    unittest.main()
