from src.agent.states import (
    ChallengeStatus,
    ClaimRelevanceLabel,
    ClaimRelationship,
    ClaimType,
    Confidence,
    GroupStatus,
    StepResult,
    SubQuestionKind,
    TerminationReason,
)


def test_str_enum_values_compare_to_strings():
    assert SubQuestionKind.SUPPORTING == "supporting"
    assert SubQuestionKind.ADVERSARIAL == "adversarial"
    assert ClaimType.EMPIRICAL == "empirical"
    assert ClaimType.SPECULATIVE == "speculative"
    assert ClaimRelevanceLabel.ADJACENT == "adjacent"
    assert Confidence.HIGH == "high"
    assert Confidence.MEDIUM == "medium"
    assert Confidence.LOW == "low"
    assert GroupStatus.DISPUTED == "disputed"
    assert ChallengeStatus.UNCHALLENGED == "unchallenged"
    assert StepResult.NEW_EVIDENCE == "NEW_EVIDENCE"
    assert TerminationReason.COVERAGE_MET == "COVERAGE_MET"
    assert ClaimRelationship.CONTRADICT == "CONTRADICT"


def test_enum_construction_from_string():
    assert SubQuestionKind("supporting") == SubQuestionKind.SUPPORTING
    assert ClaimType("empirical") == ClaimType.EMPIRICAL
    assert ClaimRelevanceLabel("adjacent") == ClaimRelevanceLabel.ADJACENT
    assert StepResult("CONFLICT_FOUND") == StepResult.CONFLICT_FOUND
