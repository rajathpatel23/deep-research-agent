from src.agent.evidence_store import ClaimGroup, EvidenceStore, StepRecord, SubQuestion
from src.agent.planner import ChallengeAction, SearchAction, StopAction, guided_plan, baseline_plan
from src.agent.states import (
    ChallengeStatus,
    Confidence,
    StepResult,
    SubQuestionKind,
    TerminationReason,
)


def _sq(id: str, kind=SubQuestionKind.SUPPORTING, has_evidence=False) -> SubQuestion:
    return SubQuestion(id=id, text=f"Question {id}", kind=kind, has_evidence=has_evidence)


def _store(sub_questions=None, claim_groups=None, step_history=None) -> EvidenceStore:
    store = EvidenceStore(query="test")
    store.sub_questions = sub_questions or []
    store.claim_groups = claim_groups or []
    store.step_history = step_history or []
    return store


# --- baseline ---

def test_baseline_cycles_through_sub_questions():
    store = _store([_sq("sq1"), _sq("sq2")])
    a0 = baseline_plan(store, 0)
    a1 = baseline_plan(store, 1)
    a2 = baseline_plan(store, 2)
    assert isinstance(a0, SearchAction) and a0.sub_question_id == "sq1"
    assert isinstance(a1, SearchAction) and a1.sub_question_id == "sq2"
    assert isinstance(a2, SearchAction) and a2.sub_question_id == "sq1"


def test_baseline_empty_returns_stop():
    store = _store([])
    assert isinstance(baseline_plan(store, 0), StopAction)


# --- guided: Rule 1 ---

def test_guided_searches_uncovered_first():
    store = _store([_sq("sq1", has_evidence=False), _sq("sq2", has_evidence=True)])
    action = guided_plan(store, 0, 10)
    assert isinstance(action, SearchAction)
    assert action.sub_question_id == "sq1"


# --- guided: Rule 2 ---

def test_guided_challenges_high_confidence_unchallenged():
    sq = _sq("sq1", has_evidence=True)
    group = ClaimGroup(
        id="grp1", canonical_text="Claim", scope="general", sub_question_id="sq1",
        aggregate_confidence=Confidence.HIGH,
        challenge_status=ChallengeStatus.UNCHALLENGED,
        supporting_claim_ids=["c1", "c2", "c3"],
        source_domains=["a.com", "b.com", "c.com"],
    )
    store = _store([sq], [group])
    action = guided_plan(store, 0, 10)
    assert isinstance(action, ChallengeAction)
    assert action.claim_group_id == "grp1"


def test_guided_does_not_challenge_adversarial_sub_questions():
    sq = _sq("sq1", kind=SubQuestionKind.ADVERSARIAL, has_evidence=True)
    group = ClaimGroup(
        id="grp1", canonical_text="Claim", scope="general", sub_question_id="sq1",
        aggregate_confidence=Confidence.HIGH,
        challenge_status=ChallengeStatus.UNCHALLENGED,
        supporting_claim_ids=["c1"],
        source_domains=["a.com"],
    )
    store = _store([sq], [group])
    action = guided_plan(store, 0, 10)
    # should not challenge adversarial sub-questions, should stop (coverage met or weakest search)
    assert not isinstance(action, ChallengeAction)


# --- guided: Rule 4 (diminishing returns) ---

def test_guided_stops_on_diminishing_returns():
    sq = _sq("sq1", has_evidence=True)
    stale = [
        StepRecord(step=i, action="search:sq1", sub_question_id="sq1", result=StepResult.REDUNDANT)
        for i in range(4)
    ]
    store = _store([sq], [], stale)
    action = guided_plan(store, 4, 10)
    assert isinstance(action, StopAction)
    assert action.reason == TerminationReason.DIMINISHING_RETURNS


def test_guided_stops_on_diminishing_returns_uncovered_but_exhausted():
    """Rule 4 fires even when sq2 is uncovered, if all recent steps are dead-ends on it."""
    sqs = [_sq("sq1", has_evidence=True), _sq("sq2", has_evidence=False)]
    stale = [
        StepRecord(step=i, action="search:sq2", sub_question_id="sq2", result=StepResult.DEAD_END)
        for i in range(4)
    ]
    store = _store(sqs, [], stale)
    action = guided_plan(store, 4, 10)
    # sq2 is in recent_dead_sq_ids, so Rule 1a skips it; Rule 4 fires on 4 consecutive stale
    assert isinstance(action, StopAction)
    assert action.reason == TerminationReason.DIMINISHING_RETURNS


def test_guided_does_not_stop_on_diminishing_returns_if_coverage_too_low():
    """Coverage guard: stale streak should not terminate when coverage floor is unmet."""
    sqs = [
        _sq("sq1", has_evidence=True),
        _sq("sq2", has_evidence=False),
        _sq("sq3", has_evidence=False),
        _sq("sq4", has_evidence=False),
        _sq("sq5", has_evidence=False),
    ]
    stale = [
        StepRecord(step=i, action="search:sq2", sub_question_id="sq2", result=StepResult.DEAD_END)
        for i in range(4)
    ]
    store = _store(sqs, [], stale)
    action = guided_plan(store, 4, 10, diminishing_window=4, min_coverage_for_diminishing=0.4)
    assert isinstance(action, SearchAction)


def test_guided_searches_uncovered_sq_not_yet_dead_ended():
    """Rule 1a fires for sq2 when it hasn't dead-ended yet, even with stale history on sq1."""
    sqs = [_sq("sq1", has_evidence=True), _sq("sq2", has_evidence=False)]
    stale = [
        StepRecord(step=i, action="search:sq1", sub_question_id="sq1", result=StepResult.REDUNDANT)
        for i in range(4)
    ]
    store = _store(sqs, [], stale)
    action = guided_plan(store, 4, 10)
    # sq2 has no evidence and isn't in recent_dead_sq_ids → Rule 1a fires
    assert isinstance(action, SearchAction)
    assert action.sub_question_id == "sq2"


# --- guided: Rule 5 (budget) ---

def test_guided_stops_on_budget():
    store = _store([_sq("sq1")])
    action = guided_plan(store, 10, 10)
    assert isinstance(action, StopAction)
    assert action.reason == TerminationReason.BUDGET_EXHAUSTED


# --- guided: Rule 6 (coverage met) ---

def test_guided_stops_when_all_covered_and_nothing_to_challenge():
    sq = _sq("sq1", has_evidence=True)
    group = ClaimGroup(
        id="grp1", canonical_text="Claim", scope="general", sub_question_id="sq1",
        aggregate_confidence=Confidence.LOW,
        challenge_status=ChallengeStatus.UNCHALLENGED,
    )
    store = _store([sq], [group])
    action = guided_plan(store, 0, 10)
    assert isinstance(action, StopAction)
    assert action.reason == TerminationReason.COVERAGE_MET
