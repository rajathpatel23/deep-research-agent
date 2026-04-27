from src.agent.evaluator import classify_step
from src.agent.evidence_store import ClaimGroup
from src.agent.states import GroupStatus, StepResult


def _group(id: str, domains=None, status=GroupStatus.WEAK) -> ClaimGroup:
    return ClaimGroup(
        id=id,
        canonical_text="Some claim text",
        scope="general",
        sub_question_id="sq1",
        source_domains=domains or [],
        status=status,
    )


def test_dead_end_when_no_new_claims():
    result = classify_step({"c1"}, {"c1"}, {}, {}, retrieved_results=1, extracted_claims=1)
    assert result == StepResult.DEAD_END


def test_new_evidence_when_new_group_appears():
    before = {}
    after = {"grp1": _group("grp1", domains=["site1.com"])}
    result = classify_step(set(), {"c1"}, before, after, retrieved_results=1, extracted_claims=1)
    assert result == StepResult.NEW_EVIDENCE


def test_new_evidence_when_new_domain_added():
    before = {"grp1": _group("grp1", domains=["site1.com"])}
    after = {"grp1": _group("grp1", domains=["site1.com", "site2.com"])}
    result = classify_step(set(), {"c1"}, before, after, retrieved_results=1, extracted_claims=1)
    assert result == StepResult.NEW_EVIDENCE


def test_redundant_when_no_new_domains_or_groups():
    before = {"grp1": _group("grp1", domains=["site1.com"])}
    after = {"grp1": _group("grp1", domains=["site1.com"])}
    result = classify_step(set(), {"c1"}, before, after, retrieved_results=1, extracted_claims=1)
    assert result == StepResult.REDUNDANT


def test_conflict_found_when_group_flips_to_disputed():
    before = {"grp1": _group("grp1", domains=["site1.com"], status=GroupStatus.SUPPORTED)}
    after = {"grp1": _group("grp1", domains=["site1.com"], status=GroupStatus.DISPUTED)}
    result = classify_step(set(), {"c1"}, before, after, retrieved_results=1, extracted_claims=1)
    assert result == StepResult.CONFLICT_FOUND


def test_conflict_found_for_new_disputed_group():
    before = {}
    after = {"grp1": _group("grp1", domains=["site1.com"], status=GroupStatus.DISPUTED)}
    result = classify_step(set(), {"c1"}, before, after, retrieved_results=1, extracted_claims=1)
    assert result == StepResult.CONFLICT_FOUND


def test_no_retrieval_results_classification():
    result = classify_step(set(), set(), {}, {}, retrieved_results=0, extracted_claims=0)
    assert result == StepResult.NO_RETRIEVAL_RESULTS


def test_no_extractable_claims_classification():
    result = classify_step(set(), set(), {}, {}, retrieved_results=3, extracted_claims=0)
    assert result == StepResult.NO_EXTRACTABLE_CLAIMS
