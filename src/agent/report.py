from typing import TYPE_CHECKING

from src.agent.evidence_store import EvidenceStore
from src.agent.llm_utils import clean_response
from src.agent.prompt_registry import get_prompt
from src.agent.states import GroupStatus, SubQuestionKind

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


def generate_report(store: EvidenceStore, llm: "LLMClient") -> str:
    sections: list = []
    citation_map = _build_citation_map(store)

    sections.append(f"# Research Report\n\n**Query:** {store.query}\n")

    prompt = get_prompt("report")
    try:
        summary = clean_response(
            llm.complete(
                prompt["system"],
                f"Evidence state:\n{_evidence_snapshot(store)}",
                trace={
                    "step": len(store.step_history),
                    "component": "report",
                    "query": store.query,
                },
            )
        )
        # Fallback: if summary drifts from the store, replace with deterministic version
        from src.agent.metrics import summary_grounding_rate
        if summary_grounding_rate(store, f"## Summary\n\n{summary}") < 0.3:
            summary = _deterministic_summary(store)
    except Exception:
        summary = _deterministic_summary(store)
    sections.append(f"## Summary\n\n{summary}\n")

    sections.append("## Findings\n")
    for sq in store.sub_questions:
        groups = [g for g in store.claim_groups if g.sub_question_id == sq.id]
        tag = " [adversarial]" if sq.kind == SubQuestionKind.ADVERSARIAL else ""
        sections.append(f"### {sq.text}{tag}\n")
        if not groups:
            sections.append("*No evidence found for this sub-question.*\n")
            continue
        for group in groups:
            cite_nums = _cite_refs(group.source_domains, citation_map)
            sections.append(f"**Claim:** {group.canonical_text}{cite_nums}\n")
            sections.append(
                f"- Confidence: {group.aggregate_confidence.value} | "
                f"Status: {group.status.value}\n"
            )
            if group.scope:
                sections.append(f"- Scope: {group.scope}\n")
            if group.status == GroupStatus.DISPUTED:
                sections.append("- **Note:** This claim has contradicting evidence.\n")
            sections.append("")

    disputed = [g for g in store.claim_groups if g.status == GroupStatus.DISPUTED]
    if disputed:
        sections.append("## Conflicts Surfaced\n")
        for group in disputed:
            cite_nums = _cite_refs(group.source_domains, citation_map)
            sections.append(f"- **{group.canonical_text}**{cite_nums} (scope: {group.scope})\n")
            sections.append(
                f"  - Supporting claims: {len(group.supporting_claim_ids)} | "
                f"Contradicting claims: {len(group.contradicting_claim_ids)}\n"
            )
        sections.append("")

    uncovered = [sq for sq in store.sub_questions if not sq.has_evidence]
    if uncovered:
        sections.append("## Unresolved Questions\n")
        for sq in uncovered:
            sections.append(f"- {sq.text}\n")
        sections.append("")

    sections.append("## Sources\n")
    for num, (domain, url) in sorted(citation_map.items(), key=lambda x: x[0]):
        sections.append(f"[{num}] {domain} — {url}\n")
    sections.append("")

    sections.append("## Research Process\n")
    sections.append(f"- Total steps: {len(store.step_history)}\n")
    sections.append(f"- Termination reason: {store.termination_reason or 'unknown'}\n")
    sections.append(
        f"- Sub-questions: {len(store.sub_questions)} total, "
        f"{sum(1 for sq in store.sub_questions if sq.has_evidence)} covered\n"
    )
    sections.append(f"- Claim groups: {len(store.claim_groups)}\n")
    if store.step_history:
        sections.append(f"- Step results: {', '.join(s.result.value for s in store.step_history)}\n")

    return "\n".join(sections)


def _build_citation_map(store: EvidenceStore) -> dict:
    """Returns {citation_number: (domain, url)} using first URL seen per domain."""
    domain_to_url: dict = {}
    for obs in store.observations:
        if obs.domain and obs.domain not in domain_to_url:
            domain_to_url[obs.domain] = obs.source_url

    citation_map: dict = {}
    for i, (domain, url) in enumerate(domain_to_url.items(), start=1):
        citation_map[i] = (domain, url)
    return citation_map


def _cite_refs(source_domains: list, citation_map: dict) -> str:
    """Returns inline citation string like ' [1][3]' for matching domains."""
    domain_to_num = {domain: num for num, (domain, _) in citation_map.items()}
    nums = sorted(domain_to_num[d] for d in source_domains if d in domain_to_num)
    if not nums:
        return ""
    return " " + "".join(f"[{n}]" for n in nums)


def _deterministic_summary(store: EvidenceStore) -> str:
    """Fallback summary built directly from the evidence store — used when LLM summary grounding is poor."""
    covered = sum(1 for sq in store.sub_questions if sq.has_evidence)
    disputes = sum(1 for g in store.claim_groups if g.status == GroupStatus.DISPUTED)
    high = sum(1 for g in store.claim_groups if g.aggregate_confidence.value == "high")
    lines = [
        f"Research covered {covered} of {len(store.sub_questions)} sub-questions "
        f"across {len(store.claim_groups)} claim groups.",
    ]
    if high:
        top = [g.canonical_text for g in store.claim_groups if g.aggregate_confidence.value == "high"][:3]
        lines.append("High-confidence findings: " + "; ".join(t[:80] for t in top) + ".")
    if disputes:
        lines.append(f"{disputes} claim group(s) have contradicting evidence — see Conflicts Surfaced.")
    uncovered = [sq.text for sq in store.sub_questions if not sq.has_evidence]
    if uncovered:
        lines.append(f"Unresolved: {'; '.join(uncovered[:2])}.")
    return " ".join(lines)


def _evidence_snapshot(store: EvidenceStore) -> str:
    lines = [f"Query: {store.query}", f"Sub-questions: {len(store.sub_questions)}"]
    for sq in store.sub_questions:
        groups = [g for g in store.claim_groups if g.sub_question_id == sq.id]
        covered = "covered" if sq.has_evidence else "uncovered"
        lines.append(f"  [{covered}] {sq.text} ({sq.kind.value})")
        for g in groups:
            lines.append(f"    - {g.canonical_text} [{g.aggregate_confidence.value}, {g.status.value}]")
    disputes = sum(1 for g in store.claim_groups if g.status == GroupStatus.DISPUTED)
    lines.append(f"Disputes: {disputes}")
    lines.append(f"Termination: {store.termination_reason or 'in-progress'}")
    return "\n".join(lines)
