from src.agent.evidence_store import EvidenceStore
from src.agent.states import Confidence, GroupStatus, TerminationReason


# ── process metrics ──────────────────────────────────────────────────────────

def coverage_completeness(store: EvidenceStore) -> float:
    total = len(store.sub_questions)
    return sum(1 for sq in store.sub_questions if sq.has_evidence) / total if total else 0.0


def search_efficiency(store: EvidenceStore) -> float:
    total = len(store.step_history)
    productive = sum(
        1 for s in store.step_history
        if s.result.value in ("NEW_EVIDENCE", "CONFLICT_FOUND")
    )
    return productive / total if total else 0.0


def conflict_surfacing_rate(store: EvidenceStore, report_text: str) -> float:
    detected = sum(1 for g in store.claim_groups if g.status == GroupStatus.DISPUTED)
    if detected == 0:
        return 1.0
    # Scope to ## Conflicts Surfaced section only — prevents gaming via Findings echoing disputed text
    conflicts_section = _extract_conflicts_section(report_text)
    surfaced = sum(
        1 for g in store.claim_groups
        if g.status == GroupStatus.DISPUTED
        and g.canonical_text[:40].lower() in conflicts_section.lower()
    )
    return surfaced / detected


def stopping_quality(store: EvidenceStore) -> float:
    return 1.0 if store.termination_reason == TerminationReason.DIMINISHING_RETURNS.value else 0.0


# ── report faithfulness metrics ──────────────────────────────────────────────

def summary_grounding_rate(store: EvidenceStore, report_text: str) -> float:
    """Fraction of sentences in the LLM-generated Summary that overlap with
    at least one claim group's canonical text (word overlap >= 0.15 Jaccard)."""
    summary = _extract_summary_section(report_text)
    if not summary.strip():
        return 1.0

    sentences = [s.strip() for s in summary.split(".") if len(s.strip()) > 20]
    if not sentences:
        return 1.0

    claim_word_sets = [
        set(g.canonical_text.lower().split()) for g in store.claim_groups
    ]

    grounded = 0
    for sentence in sentences:
        s_words = set(sentence.lower().split())
        for c_words in claim_word_sets:
            union = s_words | c_words
            intersection = s_words & c_words
            if union and len(intersection) / len(union) >= 0.15:
                grounded += 1
                break

    return grounded / len(sentences)


def unsupported_summary_rate(store: EvidenceStore, report_text: str) -> float:
    """Fraction of summary sentences not grounded in claim groups."""
    return 1.0 - summary_grounding_rate(store, report_text)


def unresolved_disclosure_rate(store: EvidenceStore, report_text: str) -> float:
    """When sub-questions are uncovered, checks if report explicitly lists them as unresolved."""
    uncovered = [sq for sq in store.sub_questions if not sq.has_evidence]
    if not uncovered:
        return 1.0

    unresolved_section = _extract_unresolved_section(report_text).lower()
    if not unresolved_section:
        return 0.0

    disclosed = sum(1 for sq in uncovered if sq.text.lower() in unresolved_section)
    return disclosed / len(uncovered)


def uncertainty_calibration_score(store: EvidenceStore, report_text: str) -> float:
    """Checks whether summary language reflects uncertainty when evidence is weak/incomplete."""
    summary = _extract_summary_section(report_text).lower()
    if not summary.strip():
        return 0.0

    uncertainty_markers = (
        "uncertain", "mixed", "limited", "inconclusive", "may", "might", "suggest",
        "appears", "unclear", "underexplored", "not enough evidence", "weak",
    )
    certainty_markers = (
        "proves", "definitive", "certainly", "always", "conclusive", "guarantees",
    )
    has_uncertainty = any(marker in summary for marker in uncertainty_markers)
    certainty_hits = sum(summary.count(marker) for marker in certainty_markers)

    uncovered_exists = any(not sq.has_evidence for sq in store.sub_questions)
    all_low_conf = bool(store.claim_groups) and all(
        g.aggregate_confidence == Confidence.LOW for g in store.claim_groups
    )
    must_express_uncertainty = uncovered_exists or all_low_conf

    if must_express_uncertainty:
        if has_uncertainty and certainty_hits == 0:
            return 1.0
        if has_uncertainty:
            return 0.5
        return 0.0

    # In stronger-evidence cases, avoid overly certain language but do not require uncertainty markers.
    return 1.0 if certainty_hits == 0 else 0.5


def epistemic_honesty_score(store: EvidenceStore, report_text: str) -> float:
    """Composite truthfulness score focused on grounding, disclosure, and calibrated certainty."""
    grounding = summary_grounding_rate(store, report_text)
    unresolved = unresolved_disclosure_rate(store, report_text)
    uncertainty = uncertainty_calibration_score(store, report_text)
    return 0.5 * grounding + 0.3 * unresolved + 0.2 * uncertainty


def source_diversity(store: EvidenceStore) -> float:
    """Mean number of distinct source domains per claim group.
    Higher = better-corroborated claims."""
    if not store.claim_groups:
        return 0.0
    return sum(len(g.source_domains) for g in store.claim_groups) / len(store.claim_groups)


def confidence_calibration(store: EvidenceStore) -> float:
    """Check whether confidence tiers have increasing source domain counts:
    high > medium > low. Returns 1.0 if fully ordered, 0.5 if partially, 0.0 if not."""
    tier_domains: dict = {Confidence.HIGH: [], Confidence.MEDIUM: [], Confidence.LOW: []}
    for g in store.claim_groups:
        tier_domains[g.aggregate_confidence].append(len(g.source_domains))

    avgs = {}
    for tier, counts in tier_domains.items():
        avgs[tier] = sum(counts) / len(counts) if counts else 0.0

    high_gt_low = avgs[Confidence.HIGH] >= avgs[Confidence.LOW]
    high_gt_med = avgs[Confidence.HIGH] >= avgs[Confidence.MEDIUM]
    med_gt_low = avgs[Confidence.MEDIUM] >= avgs[Confidence.LOW]

    if high_gt_med and med_gt_low:
        return 1.0
    if high_gt_low:
        return 0.5
    return 0.0


# ── aggregate ────────────────────────────────────────────────────────────────

def compute_metrics(store: EvidenceStore, report_text: str) -> dict:
    return {
        "coverage_completeness": round(coverage_completeness(store), 3),
        "search_efficiency": round(search_efficiency(store), 3),
        "conflict_surfacing_rate": round(conflict_surfacing_rate(store, report_text), 3),
        "stopping_quality": round(stopping_quality(store), 3),
        "summary_grounding_rate": round(summary_grounding_rate(store, report_text), 3),
        "unsupported_summary_rate": round(unsupported_summary_rate(store, report_text), 3),
        "unresolved_disclosure_rate": round(unresolved_disclosure_rate(store, report_text), 3),
        "uncertainty_calibration_score": round(uncertainty_calibration_score(store, report_text), 3),
        "epistemic_honesty_score": round(epistemic_honesty_score(store, report_text), 3),
        "source_diversity_mean": round(source_diversity(store), 3),
        "confidence_calibration": round(confidence_calibration(store), 3),
    }


# ── helpers ──────────────────────────────────────────────────────────────────

def _extract_conflicts_section(report_text: str) -> str:
    lines = report_text.split("\n")
    in_section = False
    out = []
    for line in lines:
        if line.strip().startswith("## Conflicts Surfaced"):
            in_section = True
            continue
        if in_section and line.strip().startswith("##"):
            break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()


def _extract_summary_section(report_text: str) -> str:
    lines = report_text.split("\n")
    in_summary = False
    summary_lines = []
    for line in lines:
        if line.strip().startswith("## Summary"):
            in_summary = True
            continue
        if in_summary and line.strip().startswith("##"):
            break
        if in_summary:
            summary_lines.append(line)
    return "\n".join(summary_lines).strip()


def _extract_unresolved_section(report_text: str) -> str:
    lines = report_text.split("\n")
    in_section = False
    out = []
    for line in lines:
        if line.strip().startswith("## Unresolved Questions"):
            in_section = True
            continue
        if in_section and line.strip().startswith("##"):
            break
        if in_section:
            out.append(line)
    return "\n".join(out).strip()
