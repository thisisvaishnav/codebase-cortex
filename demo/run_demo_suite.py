"""Codebase Cortex — Hackathon Demo & Verification Suite.

Runs end-to-end verification of all 4 demo scenarios:
1. Scenario 1: Senior dev merges PR introducing Redis cache -> ADR-002 auto-indexed.
2. Scenario 2: Junior dev opens PR replacing Redis with in-memory map -> cortex-detect flags violation, tags @senior-dev, Qodo declines patch.
3. Scenario 3: Contributor opens Issue proposing architecture change -> pre-flight warning posted.
4. Scenario 4: Natural language queries on Dashboard demonstrating decision recall and multi-hop lineage.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from cortex_vector_mcp.explain import explain_query, trace_adr_lineage
from cortex_vector_mcp.schema import ADR
from cortex_vector_mcp.store import Store
from sandbox.qodo.qodo_resolver import QodoFinding, check_architectural_veto, format_inline_reply, resolve_qodo_findings


def print_banner(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def run_scenario_1(store: Store) -> None:
    print_banner("DEMO SCENARIO 1: Senior Dev Merges PR #89 (Redis Cache) -> ADR-002 Auto-Indexed")

    adr_payload = {
        "id": "ADR-002",
        "title": "Redis for Distributed Session Persistence",
        "author": "senior-dev",
        "date": "2026-05-15",
        "status": "ACTIVE",
        "merged_pr": 89,
        "reasoning": "Pod resilience in Kubernetes and sub-2ms response latency under 10k concurrent active sessions.",
        "invariants": ["Session state and token blacklists MUST never be stored in process memory. They MUST be stored in the shared Redis cache layer."],
        "alternatives": ["Postgres session tables", "In-process local map"],
        "scope_files": ["src/cache/session.py"],
    }

    print(" -> Ingesting PR #89 decision record into cortex-vector store...")
    stored_adr = store.upsert_decision(adr_payload)

    print(f" ✅ Success: Indexed {stored_adr.id} ({stored_adr.status})")
    print(f"    Author: @{stored_adr.author} | Date: {stored_adr.date} | Merged PR: #{stored_adr.merged_pr}")
    print(f"    Invariant: {stored_adr.invariants[0]}")
    assert store.count() >= 1
    assert store.get_decision("ADR-002") is not None


def run_scenario_2(store: Store) -> None:
    print_banner("DEMO SCENARIO 2: Junior Dev Opens PR #142 (In-Memory Map) -> Violation & Escalation")

    finding = QodoFinding(
        id="1998877701",
        thread_id="thread_142",
        severity="WARNING",
        file="src/cache/session.py",
        line=12,
        title="In-process session optimization",
        suggestion="Replace Redis network call with an in-process local map for faster session access.",
    )

    print(" -> Running Stage 1 dense candidate retrieval against cortex-vector...")
    candidates = store.search_decisions(
        query=f"{finding.title} {finding.suggestion}",
        paths=[finding.file],
        threshold=0.20 if store.backend == "lexical" else 0.50,
        include_superseded=False,
    )
    print(f"    Found {len(candidates)} candidate ADR match(es): {[c['adr']['id'] for c in candidates]}")

    print(" -> Running Stage 2 invariant cross-encoder & architectural veto check...")
    declined, adr, confidence, explanation = check_architectural_veto(finding, store)

    print(f" 🛑 Architectural Veto Triggered: {declined}")
    print(f"    Violated Decision: {adr.id if adr else 'None'} ({adr.title if adr else ''})")
    print(f"    Conflict Confidence: {confidence}%")
    print(f"    CODEOWNERS Escalation Target: @{adr.author if adr else 'senior-dev'}")

    reply = format_inline_reply(
        finding,
        action="declined-architectural",
        adr=adr,
        confidence=confidence,
        conflict_explanation=explanation,
    )

    print("\n --- Formatted Inline GitHub Review Reply ---")
    print(reply)
    assert declined is True
    assert adr is not None and adr.id == "ADR-002"


def run_scenario_3(store: Store) -> None:
    print_banner("DEMO SCENARIO 3: Contributor Opens Issue #45 -> Pre-Flight Warning Posted")

    issue_file = Path("demo/scenario-3-issue/issue_body.md")
    issue_text = issue_file.read_text(encoding="utf-8") if issue_file.exists() else "Proposal to replace Redis session store with local dict cache"

    print(" -> Pre-flight scanning Issue #45 proposal text...")
    candidates = store.search_decisions(
        query=issue_text,
        paths=["src/cache/session.py"],
        threshold=0.20 if store.backend == "lexical" else 0.50,
        include_superseded=False,
    )

    matched_adr = candidates[0]["adr"] if candidates else None
    print(f" ✅ Matched Prior Active Decision: {matched_adr['id'] if matched_adr else 'None'}")

    comment = (
        "<!-- codebase-cortex:pr-analysis -->\n"
        "💡 **Codebase Cortex — Issue Pre-Flight Architectural Scan**\n\n"
        f"This proposal touches architecture governed by an active decision record:\n\n"
        f"- **Prior Decision:** [{matched_adr['id']}: {matched_adr['title']}](docs/adr/)\n"
        f"- **Decided by @{matched_adr['author']} · {matched_adr['date']} (PR #{matched_adr['merged_pr']})**\n"
        f"- **Invariant in force:** {matched_adr['invariants'][0]}\n\n"
        f"**Rationale:** {matched_adr['reasoning']}\n\n"
        f"*Note for contributor:* Please align with @{matched_adr['author']} before opening a PR modifying session cache boundaries."
    )

    print("\n --- Formatted Pre-Flight Issue Comment ---")
    print(comment)
    assert matched_adr is not None and matched_adr["id"] == "ADR-002"


def run_scenario_4(store: Store) -> None:
    print_banner("DEMO SCENARIO 4: Natural Language Queries & Multi-Hop Lineage Recall")

    # Add a superseded ADR to test multi-hop lineage
    adr5_payload = {
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
    store.upsert_decision(adr5_payload)
    store.update_status("ADR-002", "SUPERSEDED", superseded_by_adr="ADR-005", superseded_by_pr=134)

    queries = [
        "Why did we choose Redis over Postgres for session persistence?",
        "What is our policy on session token persistence?",
    ]

    for q in queries:
        print(f"\n ❓ Query: \"{q}\"")
        res = explain_query(store, query=q)
        print(" 💬 Answer Summary:")
        lines = res["answer"].splitlines()
        for line in lines[:8]:
            print(f"    {line}")
        print(f"    Lineage Chain Traced: {[a['id'] for a in res['lineage']]}")
        assert len(res["lineage"]) >= 1


def main() -> int:
    print("\n" + "🚀" * 40)
    print("  CODEBASE CORTEX — HACKATHON DEMO & VERIFICATION SUITE")
    print("🚀" * 40)

    with tempfile.TemporaryDirectory() as temp_dir:
        store = Store(persist_dir=Path(temp_dir))
        run_scenario_1(store)
        run_scenario_2(store)
        run_scenario_3(store)
        run_scenario_4(store)

    print("\n" + "🎉" * 40)
    print("  ALL 4 DEMO SCENARIOS PASSED & VERIFIED SUCCESSFULLY!")
    print("🎉" * 40 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
