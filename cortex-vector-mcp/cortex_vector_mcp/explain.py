"""Institutional Q&A & Multi-Hop Lineage Reasoning Engine for cortex-explain.

Provides semantic retrieval over active and superseded ADRs, multi-hop
lineage tracing along `superseded_by_adr` relationships (oldest -> newest),
and structured markdown answer generation attributing decisions to authors,
timestamps, PRs, and trade-offs.
"""

from __future__ import annotations

import logging
from typing import Any

from .schema import ADR
from .store import Store

log = logging.getLogger(__name__)


def trace_adr_lineage(store: Store, adr_id: str, max_hops: int = 10) -> list[ADR]:
    """Walk an ADR's lineage in both directions to reconstruct its full history.

    Args:
        store: vector memory store.
        adr_id: target ADR ID (e.g. "ADR-002").
        max_hops: safety limit to prevent cycles.

    Returns:
        List of ADR objects ordered chronologically (oldest -> newest).
    """
    all_adrs = {a.id.upper(): a for a in store.list_decisions()}
    target_id = adr_id.strip().upper()

    if target_id not in all_adrs:
        return []

    visited: set[str] = set()
    chain_set: set[str] = {target_id}

    # 1. Walk Forward: follow superseded_by_adr pointers to the tip (ACTIVE)
    curr_id = target_id
    hops = 0
    while curr_id and curr_id in all_adrs and curr_id not in visited and hops < max_hops:
        visited.add(curr_id)
        chain_set.add(curr_id)
        adr = all_adrs[curr_id]
        if adr.status == "ACTIVE" or not adr.superseded_by_adr:
            break
        curr_id = adr.superseded_by_adr.upper()
        hops += 1

    # 2. Walk Backward: find predecessors where superseded_by_adr points to nodes in chain
    visited_back: set[str] = set()
    changed = True
    hops_back = 0
    while changed and hops_back < max_hops:
        changed = False
        hops_back += 1
        for aid, adr in list(all_adrs.items()):
            if aid in chain_set:
                continue
            if adr.superseded_by_adr and adr.superseded_by_adr.upper() in chain_set:
                chain_set.add(aid)
                changed = True

    # 3. Sort chain chronologically: date first, then ID
    result_adrs = [all_adrs[aid] for aid in chain_set if aid in all_adrs]

    def _sort_key(a: ADR) -> tuple[str, str]:
        return (a.date or "", a.id or "")

    result_adrs.sort(key=_sort_key)
    return result_adrs


def format_explain_response(query: str, candidates: list[dict[str, Any]], lineage_chain: list[ADR]) -> str:
    """Format a contextual response attributing decisions to authors, dates, and trade-offs.

    Adheres strictly to skills/cortex-explain/SKILL.md response format.
    """
    if not candidates or not lineage_chain:
        return (
            f"**Decision Not Found**\n\n"
            f"The query *\"{query}\"* did not match any architectural decision records in Cortex memory.\n\n"
            f"*Suggestion:* If this represents a new or unrecorded decision, consider opening a PR "
            f"with the Codebase Cortex Decision Record template to index it."
        )

    # Tip of lineage chain (most recent / active record)
    active_tip = next((a for a in reversed(lineage_chain) if a.status == "ACTIVE"), lineage_chain[-1])
    
    sections: list[str] = []

    # 1. Current answer summary
    if active_tip.status == "ACTIVE":
        rule_summary = active_tip.invariants[0] if active_tip.invariants else active_tip.title
        sections.append(f"**Current answer:** {active_tip.title}. Rule in force: {rule_summary}")
    else:
        sections.append(f"**Current answer:** Decision {active_tip.id} ({active_tip.title}) is currently marked {active_tip.status}.")

    # 2. Lineage details for each decision in the chain
    sections.append("\n### Decision Lineage & Trade-offs\n")
    for adr in lineage_chain:
        item_lines = [
            f"- **Decision:** {adr.id} — {adr.title}",
            f"- **Rationale:** {adr.reasoning or 'No explicit rationale recorded.'}",
        ]
        if adr.alternatives:
            alts_str = "; ".join(adr.alternatives)
            item_lines.append(f"- **Alternatives rejected:** {alts_str}")
        else:
            item_lines.append("- **Alternatives rejected:** None specified")

        meta_line = f"- **Author:** @{adr.author} · **Date:** {adr.date} · **Status:** {adr.status}"
        if adr.merged_pr:
            meta_line += f" · **Merged PR:** #{adr.merged_pr}"
        item_lines.append(meta_line)

        if adr.status == "SUPERSEDED":
            sup_by = adr.superseded_by_adr or "a later ADR"
            pr_info = f" in PR #{adr.superseded_by_pr}" if adr.superseded_by_pr else ""
            item_lines.append(f"- **Lineage:** {adr.id} (SUPERSEDED by {sup_by}{pr_info})")
        else:
            item_lines.append(f"- **Lineage:** {adr.id} ({adr.status}) — active policy tip")

        sections.append("\n".join(item_lines) + "\n")

    # 3. Active Invariant
    if active_tip.invariants:
        inv_str = "\n".join(f"- {inv}" for inv in active_tip.invariants)
        sections.append(f"**Invariant still in force:**\n{inv_str}")

    return "\n\n".join(sections)


def explain_query(
    store: Store,
    query: str,
    paths: list[str] | None = None,
    threshold: float = 0.50,
) -> dict[str, Any]:
    """Execute natural language Q&A query over ADR lineage.

    Args:
        store: vector store.
        query: developer's natural language question.
        paths: optional path filters/scope hints.
        threshold: retrieval similarity floor (default 0.50 for high recall).

    Returns:
        Dict with keys: `answer`, `lineage`, `candidates`, `query`.
    """
    # Lexical TF-IDF vectors have lower raw magnitude than dense MiniLM embeddings;
    # calibrate threshold when running on the lexical fallback backend.
    effective_threshold = 0.10 if store.backend == "lexical" else threshold

    candidates = store.search_decisions(
        query=query,
        paths=paths,
        threshold=effective_threshold,
        limit=5,
        include_superseded=True,
    )

    if not candidates:
        ans = format_explain_response(query, [], [])
        return {
            "answer": ans,
            "lineage": [],
            "candidates": [],
            "query": query,
        }

    # Collect lineage chains for top candidate ADRs
    seen_ids: set[str] = set()
    full_lineage: list[ADR] = []

    for cand in candidates:
        adr_dict = cand.get("adr", {})
        aid = adr_dict.get("id")
        if not aid or aid in seen_ids:
            continue
        chain = trace_adr_lineage(store, aid)
        for adr in chain:
            if adr.id not in seen_ids:
                seen_ids.add(adr.id)
                full_lineage.append(adr)

    # Sort combined lineage chronologically
    full_lineage.sort(key=lambda a: (a.date or "", a.id or ""))

    answer_text = format_explain_response(query, candidates, full_lineage)

    return {
        "answer": answer_text,
        "lineage": [a.to_dict() for a in full_lineage],
        "candidates": candidates,
        "query": query,
    }
