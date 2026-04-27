from typing import Dict, Set

from src.agent.evidence_store import ClaimGroup
from src.agent.states import GroupStatus, StepResult


def classify_step(
    claims_before: Set[str],
    claims_after: Set[str],
    groups_before: Dict[str, ClaimGroup],
    groups_after: Dict[str, ClaimGroup],
    retrieved_results: int,
    extracted_claims: int,
) -> StepResult:
    if retrieved_results == 0:
        return StepResult.NO_RETRIEVAL_RESULTS
    if extracted_claims == 0:
        return StepResult.NO_EXTRACTABLE_CLAIMS

    new_claim_ids = claims_after - claims_before
    if not new_claim_ids:
        return StepResult.DEAD_END

    # any group that flipped to disputed in this step
    for gid, group in groups_after.items():
        prev = groups_before.get(gid)
        if group.status == GroupStatus.DISPUTED and (prev is None or prev.status != GroupStatus.DISPUTED):
            return StepResult.CONFLICT_FOUND

    # new claims present — check if they brought new domains or new groups
    new_groups = set(groups_after) - set(groups_before)
    new_domains = any(
        set(groups_after[gid].source_domains) > set(groups_before[gid].source_domains)
        for gid in groups_after
        if gid in groups_before
    )
    if not new_domains and not new_groups:
        return StepResult.REDUNDANT

    return StepResult.NEW_EVIDENCE
