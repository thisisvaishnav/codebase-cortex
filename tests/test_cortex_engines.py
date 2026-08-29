#!/usr/bin/env python3
"""Unit and integration test suite for cortex-detect & cortex-notify engines."""

import json
import os
import unittest

from sandbox.fitness import _fitness_common as fc, check_import_boundaries, check_banned_dependencies, run_all
from sandbox.notify import notify_engine


class TestCortexFitnessEngine(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.rules_path = os.path.join(self.repo_root, "sandbox", "fitness", "fitness_rules.json")
        self.rules = fc.load_rules(self.rules_path)

    def test_compliant_base_passes_fitness(self):
        base_dir = os.path.join(self.repo_root, "demo", "fixtures", "base")
        if not os.path.exists(base_dir):
            self.skipTest("base fixture directory missing")
        results = run_all.run_all(base_dir, self.rules)
        passed = all(item["passed"] for item in results)
        self.assertTrue(passed, "Base fixture should pass all fitness checks without violations")

    def test_violation_scenario_flags_in_process_state(self):
        violation_dir = os.path.join(self.repo_root, "demo", "scenario-2-violation", "files")
        if not os.path.exists(violation_dir):
            self.skipTest("scenario-2-violation directory missing")
        results = run_all.run_all(violation_dir, self.rules)
        in_process_check = next(r for r in results if r["name"] == "no-in-process-session-state")
        self.assertFalse(in_process_check["passed"])
        violated_vars = [v["message"] for v in in_process_check["violations"]]
        self.assertTrue(any("_SESSIONS" in msg for msg in violated_vars))
        self.assertTrue(any("_REVOKED_JTI" in msg for msg in violated_vars))


class TestCortexNotifyEngine(unittest.TestCase):
    def setUp(self):
        self.sample_codeowners = """
# Global maintainers
* @lead-maintainer @senior-dev

# Path specific rules
/src/core/ @senior-dev
/src/cache/ @senior-dev
/config/ @lead-maintainer
"""

    def test_codeowners_parsing_last_matching_rule_wins(self):
        # /src/cache/ session.py should match /src/cache/ winning rule (@senior-dev)
        owners = notify_engine.resolve_codeowners(self.sample_codeowners, ["src/cache/session.py"])
        self.assertEqual(owners, ["@senior-dev"])

        # /config/ settings.py should match /config/ winning rule (@lead-maintainer)
        config_owners = notify_engine.resolve_codeowners(self.sample_codeowners, ["config/settings.py"])
        self.assertEqual(config_owners, ["@lead-maintainer"])

        # Root file matches fallback *
        root_owners = notify_engine.resolve_codeowners(self.sample_codeowners, ["README.md"])
        self.assertEqual(root_owners, ["@lead-maintainer", "@senior-dev"])

    def test_mention_hygiene_and_self_tagging(self):
        # PR author is junior-dev; ADR author senior-dev; codeowner senior-dev
        mentions = notify_engine.resolve_mentions("senior-dev", ["@senior-dev"], "junior-dev", 0.90)
        self.assertEqual(mentions, ["@senior-dev"])

        # PR author is senior-dev (author self-tag prevention)
        self_tag_mentions = notify_engine.resolve_mentions("senior-dev", ["@senior-dev"], "senior-dev", 0.90)
        self.assertEqual(self_tag_mentions, [])

        # Low confidence (<0.80) yields zero mentions
        advisory_mentions = notify_engine.resolve_mentions("senior-dev", ["@senior-dev"], "junior-dev", 0.70)
        self.assertEqual(advisory_mentions, [])

    def test_comment_formatting_and_dedup_hash(self):
        verdict = {
            "has_violation": True,
            "confidence": 0.92,
            "classification": "HARD_VIOLATION",
            "violated_adr_id": "ADR-002",
            "violated_adr_title": "Redis for Distributed Session Persistence",
            "author": "senior-dev",
            "reason": "Replaces Redis with dict",
            "affected_files": ["src/cache/session.py"],
        }
        res1 = notify_engine.format_comment(verdict, "junior-dev", self.sample_codeowners)
        self.assertEqual(res1["action"], "create")
        self.assertIn("<!-- codebase-cortex:pr-analysis -->", res1["body"])
        self.assertIn("<!-- cortex:hash:", res1["body"])
        self.assertIn("@senior-dev", res1["body"])

        # Re-running with standing comment returns action "skip"
        res2 = notify_engine.format_comment(verdict, "junior-dev", self.sample_codeowners, standing_comment=res1["body"])
        self.assertEqual(res2["action"], "skip")

    def test_escalation_ratchet(self):
        standing_violation_comment = (
            "<!-- codebase-cortex:pr-analysis -->\n"
            "⚠️ **Codebase Cortex — Architectural Conflict Detected**\n"
            "<!-- cortex:hash:oldhash12345 -->"
        )
        clean_verdict = {
            "has_violation": False,
            "confidence": 0.10,
            "classification": "COMPLIANT",
            "affected_files": ["src/cache/session.py"],
        }
        res = notify_engine.format_comment(clean_verdict, "junior-dev", self.sample_codeowners, standing_comment=standing_violation_comment)
        self.assertEqual(res["action"], "update")
        self.assertIn("Previous architectural conflict has been resolved", res["body"])


if __name__ == "__main__":
    unittest.main()
