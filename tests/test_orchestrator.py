from src.agent.evidence_store import EvidenceStore, StepRecord, SubQuestion
from src.agent.orchestrator import _pivot_queries, _recent_sq_failure_streak
from src.agent.states import StepResult, SubQuestionKind


def _step(step: int, sq_id: str, result: StepResult) -> StepRecord:
    return StepRecord(
        step=step,
        action=f"search:{sq_id}",
        sub_question_id=sq_id,
        result=result,
    )


def test_recent_sq_failure_streak_counts_consecutive_failures():
    store = EvidenceStore(query="q")
    store.step_history.extend(
        [
            _step(0, "sq1", StepResult.NEW_EVIDENCE),
            _step(1, "sq1", StepResult.NO_EXTRACTABLE_CLAIMS),
            _step(2, "sq1", StepResult.DEAD_END),
        ]
    )
    assert _recent_sq_failure_streak(store, "sq1") == 2


def test_recent_sq_failure_streak_resets_after_progress():
    store = EvidenceStore(query="q")
    store.step_history.extend(
        [
            _step(0, "sq1", StepResult.NO_EXTRACTABLE_CLAIMS),
            _step(1, "sq1", StepResult.NEW_EVIDENCE),
            _step(2, "sq1", StepResult.NO_RETRIEVAL_RESULTS),
        ]
    )
    assert _recent_sq_failure_streak(store, "sq1") == 1


def test_recent_sq_failure_streak_ignores_other_sub_questions():
    store = EvidenceStore(query="q")
    store.step_history.extend(
        [
            _step(0, "sq1", StepResult.NO_EXTRACTABLE_CLAIMS),
            _step(1, "sq2", StepResult.NO_EXTRACTABLE_CLAIMS),
            _step(2, "sq1", StepResult.DEAD_END),
        ]
    )
    assert _recent_sq_failure_streak(store, "sq1") == 2
    assert _recent_sq_failure_streak(store, "sq2") == 1


def test_pivot_queries_tier_up_with_failure_streak():
    sq = SubQuestion(id="sq1", text="cot effectiveness across benchmarks", kind=SubQuestionKind.SUPPORTING)
    q = "is chain-of-thought effective"

    streak_0 = _pivot_queries(q, sq, 0)
    streak_1 = _pivot_queries(q, sq, 1)
    streak_2 = _pivot_queries(q, sq, 2)
    streak_3 = _pivot_queries(q, sq, 3)

    assert streak_0 == []
    assert any("ablation" in s for s in streak_1)
    assert any("arxiv" in s and "openreview" in s for s in streak_2)
    assert any("site:arxiv.org" in s for s in streak_3)
    assert any("site:openreview.net" in s for s in streak_3)


def test_pivot_queries_include_empirical_keywords_at_first_pivot():
    sq = SubQuestion(id="sq1", text="formatting vs reasoning metrics", kind=SubQuestionKind.ADVERSARIAL)
    pivots = _pivot_queries("cot disagreement", sq, 1)
    assert pivots
    assert "empirical" in pivots[0]
    assert "benchmark" in pivots[0]
