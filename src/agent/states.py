from enum import Enum


# --- Evidence domain states ---

class SubQuestionKind(str, Enum):
    SUPPORTING = "supporting"
    ADVERSARIAL = "adversarial"


class ClaimType(str, Enum):
    EMPIRICAL = "empirical"
    SPECULATIVE = "speculative"


class ClaimRelevanceLabel(str, Enum):
    DIRECT = "direct"
    ADJACENT = "adjacent"
    IRRELEVANT = "irrelevant"


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class GroupStatus(str, Enum):
    SUPPORTED = "supported"
    DISPUTED = "disputed"
    WEAK = "weak"
    SPECULATIVE = "speculative"


class ChallengeStatus(str, Enum):
    UNCHALLENGED = "unchallenged"
    CHALLENGED_NO_CONFLICT = "challenged_no_conflict"
    CHALLENGED_CONFLICT_FOUND = "challenged_conflict_found"


class StepResult(str, Enum):
    NEW_EVIDENCE = "NEW_EVIDENCE"
    CONFLICT_FOUND = "CONFLICT_FOUND"
    REDUNDANT = "REDUNDANT"
    DEAD_END = "DEAD_END"
    NO_RETRIEVAL_RESULTS = "NO_RETRIEVAL_RESULTS"
    NO_EXTRACTABLE_CLAIMS = "NO_EXTRACTABLE_CLAIMS"


class TerminationReason(str, Enum):
    DIMINISHING_RETURNS = "DIMINISHING_RETURNS"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    COVERAGE_MET = "COVERAGE_MET"


class ClaimRelationship(str, Enum):
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    COMPATIBLE = "COMPATIBLE"
    UNRELATED = "UNRELATED"
