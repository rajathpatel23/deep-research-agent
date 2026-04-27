import pytest
from src.agent.evidence_store import Claim, ClaimGroup, EvidenceStore, Observation, StepRecord, SubQuestion, _new_id
from src.agent.metrics import (
    _extract_summary_section,
    confidence_calibration,
    conflict_surfacing_rate,
    coverage_completeness,
    search_efficiency,
    source_diversity,
    stopping_quality,
    summary_grounding_rate,
)
from src.agent.states import (
    Confidence,
    GroupStatus,
    StepResult,
    SubQuestionKind,
    TerminationReason,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

def _sq(has_evidence: bool = True, kind: SubQuestionKind = SubQuestionKind.SUPPORTING) -> SubQuestion:
    return SubQuestion(id=_new_id("sq"), text="test question", kind=kind, has_evidence=has_evidence)


def _group(
    confidence: Confidence = Confidence.LOW,
    status: GroupStatus = GroupStatus.WEAK,
    domains: list = None,
    canonical: str = "test claim about topic",
    sq_id: str = "sq1",
) -> ClaimGroup:
    return ClaimGroup(
        id=_new_id("grp"),
        canonical_text=canonical,
        scope="general",
        sub_question_id=sq_id,
        aggregate_confidence=confidence,
        status=status,
        source_domains=domains or ["example.com"],
    )


def _step(result: StepResult) -> StepRecord:
    return StepRecord(step=0, action="search:sq1", sub_question_id="sq1", result=result)


def _store(**kwargs) -> EvidenceStore:
    return EvidenceStore(query="test query", **kwargs)


# ── coverage_completeness ────────────────────────────────────────────────────

def test_coverage_all_covered():
    store = _store(sub_questions=[_sq(True), _sq(True), _sq(True)])
    assert coverage_completeness(store) == 1.0


def test_coverage_partial():
    store = _store(sub_questions=[_sq(True), _sq(False), _sq(True)])
    assert coverage_completeness(store) == pytest.approx(2 / 3)


def test_coverage_none_covered():
    store = _store(sub_questions=[_sq(False), _sq(False)])
    assert coverage_completeness(store) == 0.0


def test_coverage_empty():
    store = _store(sub_questions=[])
    assert coverage_completeness(store) == 0.0


# ── search_efficiency ────────────────────────────────────────────────────────

def test_efficiency_all_productive():
    store = _store(step_history=[
        _step(StepResult.NEW_EVIDENCE),
        _step(StepResult.CONFLICT_FOUND),
    ])
    assert search_efficiency(store) == 1.0


def test_efficiency_mixed():
    store = _store(step_history=[
        _step(StepResult.NEW_EVIDENCE),
        _step(StepResult.REDUNDANT),
        _step(StepResult.NEW_EVIDENCE),
        _step(StepResult.DEAD_END),
    ])
    assert search_efficiency(store) == 0.5


def test_efficiency_none_productive():
    store = _store(step_history=[_step(StepResult.REDUNDANT), _step(StepResult.DEAD_END)])
    assert search_efficiency(store) == 0.0


def test_efficiency_empty():
    store = _store(step_history=[])
    assert search_efficiency(store) == 0.0


# ── conflict_surfacing_rate ───────────────────────────────────────────────────

def test_csr_no_conflicts():
    store = _store(claim_groups=[_group(status=GroupStatus.WEAK)])
    assert conflict_surfacing_rate(store, "any report text") == 1.0


def test_csr_conflict_surfaced():
    g = _group(status=GroupStatus.DISPUTED, canonical="retrieval augmented generation fails sometimes")
    store = _store(claim_groups=[g])
    # Conflict must appear in ## Conflicts Surfaced section, not just anywhere in the report
    report = "## Summary\n\nsome summary\n## Findings\n\n## Conflicts Surfaced\n\nretrieval augmented generation fails sometimes in practice\n## Sources"
    assert conflict_surfacing_rate(store, report) == 1.0


def test_csr_conflict_not_surfaced():
    g = _group(status=GroupStatus.DISPUTED, canonical="retrieval augmented generation fails sometimes")
    store = _store(claim_groups=[g])
    # Text appears in Summary but NOT in Conflicts Surfaced — should not count
    report = "## Summary\n\nretrieval augmented generation fails sometimes\n## Findings\n## Conflicts Surfaced\n\nnothing here"
    assert conflict_surfacing_rate(store, report) == 0.0


def test_csr_partial():
    g1 = _group(status=GroupStatus.DISPUTED, canonical="rag fails in production environments often")
    g2 = _group(status=GroupStatus.DISPUTED, canonical="embedding models miss semantic nuance always")
    store = _store(claim_groups=[g1, g2])
    # Only g1 appears in Conflicts Surfaced section
    report = "## Findings\nsome findings\n## Conflicts Surfaced\nrag fails in production environments often noted by researchers"
    assert conflict_surfacing_rate(store, report) == 0.5


# ── stopping_quality ─────────────────────────────────────────────────────────

def test_stopping_quality_diminishing_returns():
    store = _store(termination_reason=TerminationReason.DIMINISHING_RETURNS.value)
    assert stopping_quality(store) == 1.0


def test_stopping_quality_budget_exhausted():
    store = _store(termination_reason=TerminationReason.BUDGET_EXHAUSTED.value)
    assert stopping_quality(store) == 0.0


def test_stopping_quality_coverage_met():
    store = _store(termination_reason=TerminationReason.COVERAGE_MET.value)
    assert stopping_quality(store) == 0.0


# ── summary_grounding_rate ───────────────────────────────────────────────────

def test_summary_grounding_empty_summary():
    store = _store(claim_groups=[_group(canonical="rag improves accuracy")])
    report = "# Report\n\n## Findings\nsome findings"
    assert summary_grounding_rate(store, report) == 1.0


def test_summary_grounding_grounded():
    g = _group(canonical="retrieval augmented generation reduces hallucinations significantly")
    store = _store(claim_groups=[g])
    report = (
        "## Summary\n\n"
        "Retrieval augmented generation reduces hallucinations in practice. "
        "The evidence supports this across multiple domains.\n"
        "## Findings"
    )
    assert summary_grounding_rate(store, report) > 0.0


def test_summary_grounding_ungrounded():
    g = _group(canonical="completely unrelated claim about weather patterns")
    store = _store(claim_groups=[g])
    report = (
        "## Summary\n\n"
        "Quantum computing transforms pharmaceutical drug discovery exponentially.\n"
        "## Findings"
    )
    assert summary_grounding_rate(store, report) == 0.0


def test_extract_summary_section():
    report = "# Title\n\n## Summary\n\nThis is the summary text.\n\n## Findings\n\nMore text."
    summary = _extract_summary_section(report)
    assert "This is the summary text" in summary
    assert "Findings" not in summary


# ── source_diversity ─────────────────────────────────────────────────────────

def test_source_diversity_single_domain():
    store = _store(claim_groups=[
        _group(domains=["a.com"]),
        _group(domains=["b.com"]),
    ])
    assert source_diversity(store) == 1.0


def test_source_diversity_multiple_domains():
    store = _store(claim_groups=[
        _group(domains=["a.com", "b.com", "c.com"]),
        _group(domains=["d.com"]),
    ])
    assert source_diversity(store) == pytest.approx(2.0)


def test_source_diversity_empty():
    store = _store(claim_groups=[])
    assert source_diversity(store) == 0.0


# ── confidence_calibration ───────────────────────────────────────────────────

def test_calibration_perfect_ordering():
    store = _store(claim_groups=[
        _group(confidence=Confidence.HIGH, domains=["a.com", "b.com", "c.com"]),
        _group(confidence=Confidence.MEDIUM, domains=["d.com", "e.com"]),
        _group(confidence=Confidence.LOW, domains=["f.com"]),
    ])
    assert confidence_calibration(store) == 1.0


def test_calibration_only_high_gt_low():
    store = _store(claim_groups=[
        _group(confidence=Confidence.HIGH, domains=["a.com", "b.com", "c.com"]),
        _group(confidence=Confidence.MEDIUM, domains=["d.com"]),
        _group(confidence=Confidence.LOW, domains=["e.com", "f.com"]),
    ])
    assert confidence_calibration(store) == 0.5


def test_calibration_no_ordering():
    store = _store(claim_groups=[
        _group(confidence=Confidence.HIGH, domains=["a.com"]),
        _group(confidence=Confidence.LOW, domains=["b.com", "c.com", "d.com"]),
    ])
    assert confidence_calibration(store) == 0.0


def test_calibration_missing_tiers():
    # Only low-confidence groups — no ordering violation possible, default to 1.0
    store = _store(claim_groups=[
        _group(confidence=Confidence.LOW, domains=["a.com"]),
        _group(confidence=Confidence.LOW, domains=["b.com"]),
    ])
    # high=0, medium=0, low=1 → high >= low is False → 0.0
    assert confidence_calibration(store) == 0.0
