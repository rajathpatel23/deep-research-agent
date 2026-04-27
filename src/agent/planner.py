from enum import Enum
from typing import Union

from pydantic import BaseModel

from src.agent.evidence_store import EvidenceStore
from src.agent.states import (
    ChallengeStatus,
    Confidence,
    StepResult,
    SubQuestionKind,
    TerminationReason,
)


class ActionType(str, Enum):
    SEARCH = "search"
    CHALLENGE = "challenge"
    STOP = "stop"


class SearchAction(BaseModel):
    type: ActionType = ActionType.SEARCH
    sub_question_id: str = ""


class ChallengeAction(BaseModel):
    type: ActionType = ActionType.CHALLENGE
    claim_group_id: str = ""


class StopAction(BaseModel):
    type: ActionType = ActionType.STOP
    reason: TerminationReason = TerminationReason.BUDGET_EXHAUSTED


PlannerAction = Union[SearchAction, ChallengeAction, StopAction]

def baseline_plan(store: EvidenceStore, step: int) -> PlannerAction:
    """Fixed-order: cycle through sub-questions. Never challenges. Stops only on budget."""
    if not store.sub_questions:
        return StopAction(reason=TerminationReason.COVERAGE_MET)
    idx = step % len(store.sub_questions)
    return SearchAction(sub_question_id=store.sub_questions[idx].id)


def guided_plan(
    store: EvidenceStore,
    step: int,
    max_steps: int,
    diminishing_window: int = 4,
    min_coverage_for_diminishing: float = 0.4,
) -> PlannerAction:
    """Evidence-driven priority rules."""
    if step >= max_steps:
        return StopAction(reason=TerminationReason.BUDGET_EXHAUSTED)

    # Compute recent dead-end set once — used by Rule 1 and Rule 4
    window = max(len(store.sub_questions), 1)
    recent_dead_sq_ids = {
        s.sub_question_id for s in store.step_history[-window:]
        if s.result == StepResult.DEAD_END
    }
    stale = {
        StepResult.REDUNDANT,
        StepResult.DEAD_END,
        StepResult.NO_RETRIEVAL_RESULTS,
        StepResult.NO_EXTRACTABLE_CLAIMS,
    }

    # Rule 1a: uncovered sub-questions not recently dead-ended
    for sq in store.sub_questions:
        if not sq.has_evidence and sq.id not in recent_dead_sq_ids:
            return SearchAction(sub_question_id=sq.id)

    # Rule 4: diminishing returns — fires when all uncovered sqs have dead-ended recently
    # (or all sqs are covered). Placed here so persistent dead-ends stop the run rather
    # than burning the full budget via Rule 1b fallback.
    coverage = (
        sum(1 for sq in store.sub_questions if sq.has_evidence) / len(store.sub_questions)
        if store.sub_questions
        else 0.0
    )
    if len(store.step_history) >= diminishing_window:
        if (
            coverage >= min_coverage_for_diminishing
            and all(s.result in stale for s in store.step_history[-diminishing_window:])
        ):
            return StopAction(reason=TerminationReason.DIMINISHING_RETURNS)

    # Rule 1b: fallback — all uncovered sqs have dead-ended recently but last N steps
    # aren't all stale yet; try the first uncovered sq anyway
    for sq in store.sub_questions:
        if not sq.has_evidence:
            return SearchAction(sub_question_id=sq.id)

    # Rule 2: challenge medium-or-high confidence supporting claims with 2+ domains, not yet challenged
    for group in store.claim_groups:
        sq = next((s for s in store.sub_questions if s.id == group.sub_question_id), None)
        if (
            group.aggregate_confidence in (Confidence.MEDIUM, Confidence.HIGH)
            and len(group.source_domains) >= 2
            and group.challenge_status == ChallengeStatus.UNCHALLENGED
            and sq is not None
            and sq.kind == SubQuestionKind.SUPPORTING
        ):
            return ChallengeAction(claim_group_id=group.id)

    # Rule 3: weakest sub-question by supporting claim count
    weakest = min(
        store.sub_questions,
        key=lambda sq: sum(
            len(g.supporting_claim_ids)
            for g in store.claim_groups
            if g.sub_question_id == sq.id
        ),
    )

    # Rule 6: all covered, nothing left to challenge
    all_covered = all(sq.has_evidence for sq in store.sub_questions)
    has_unchallenged_high = any(
        g.aggregate_confidence in (Confidence.MEDIUM, Confidence.HIGH)
        and len(g.source_domains) >= 2
        and g.challenge_status == ChallengeStatus.UNCHALLENGED
        for g in store.claim_groups
    )
    if all_covered and not has_unchallenged_high:
        return StopAction(reason=TerminationReason.COVERAGE_MET)

    return SearchAction(sub_question_id=weakest.id)
