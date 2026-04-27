import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from src.agent.states import (
    ChallengeStatus,
    ClaimRelationship,
    ClaimRelevanceLabel,
    ClaimType,
    Confidence,
    GroupStatus,
    StepResult,
    SubQuestionKind,
)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _jaccard(a: str, b: str) -> float:
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


class SubQuestion(BaseModel):
    id: str
    text: str
    kind: SubQuestionKind
    has_evidence: bool = False


class Observation(BaseModel):
    id: str
    step: int
    sub_question_id: str
    source_url: str
    source_title: str
    domain: str
    snippet: str
    domain_score: float = 0.5


class Claim(BaseModel):
    id: str
    text: str
    scope: str
    claim_type: ClaimType
    source_observation_id: str
    verbatim: str
    sub_question_id: str
    step: int
    relevance_label: ClaimRelevanceLabel = ClaimRelevanceLabel.DIRECT


class ClaimGroup(BaseModel):
    id: str
    canonical_text: str
    scope: str
    sub_question_id: str
    supporting_claim_ids: List[str] = Field(default_factory=list)
    contradicting_claim_ids: List[str] = Field(default_factory=list)
    source_domains: List[str] = Field(default_factory=list)
    aggregate_confidence: Confidence = Confidence.LOW
    status: GroupStatus = GroupStatus.WEAK
    challenge_status: ChallengeStatus = ChallengeStatus.UNCHALLENGED


class StepRecord(BaseModel):
    step: int
    action: str
    sub_question_id: str
    result: StepResult
    retrieved_results: int = 0
    observations_added: int = 0
    extracted_claims: int = 0
    result_reason: str = ""
    recovery_attempts: int = 0
    recovery_strategy: str = ""
    query_variants_tried: int = 0
    rerank_in_count: int = 0
    rerank_out_count: int = 0
    claims_filtered_out: int = 0
    adjacent_claims_added: int = 0
    direct_claims_added: int = 0
    direct_claim_conversion_rate: float = 0.0
    query_compression_attempts: int = 0
    query_compression_llm_successes: int = 0
    query_compression_fallback_truncations: int = 0
    query_compression_chars_saved: int = 0


class LLMCallRecord(BaseModel):
    id: str
    step: int
    component: str
    provider: str
    model: str
    system_prompt: str
    user_prompt: str
    response_text: str
    meta: dict = Field(default_factory=dict)
    timestamp_utc: str


class EvidenceStore(BaseModel):
    query: str
    sub_questions: List[SubQuestion] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)
    claims: List[Claim] = Field(default_factory=list)
    adjacent_claims: List[Claim] = Field(default_factory=list)
    claim_groups: List[ClaimGroup] = Field(default_factory=list)
    step_history: List[StepRecord] = Field(default_factory=list)
    llm_calls: List[LLMCallRecord] = Field(default_factory=list)
    conflict_candidates_considered: int = 0
    conflict_llm_checks: int = 0
    conflict_scope_filtered: int = 0
    conflict_contradictions_found: int = 0
    termination_reason: Optional[str] = None

    def update(self, new_claims: List[Claim], llm=None, min_direct_domain_score: float = 0.6) -> None:
        for claim in new_claims:
            domain_score = self._domain_score_for_claim(claim)
            if (
                claim.relevance_label == ClaimRelevanceLabel.DIRECT
                and domain_score < min_direct_domain_score
            ):
                claim.relevance_label = ClaimRelevanceLabel.ADJACENT
            if claim.relevance_label != ClaimRelevanceLabel.DIRECT:
                self.adjacent_claims.append(claim)
                continue
            self.claims.append(claim)
            group = self._find_or_create_group(claim, llm)
            if claim.id not in group.supporting_claim_ids:
                group.supporting_claim_ids.append(claim.id)
            domain = self._domain_for_claim(claim)
            if domain and domain not in group.source_domains:
                group.source_domains.append(domain)
            self._update_group_confidence(group)
            for sq in self.sub_questions:
                if sq.id == claim.sub_question_id:
                    sq.has_evidence = True
            if llm is not None:
                self._detect_conflicts(claim, group, llm)

    def _find_or_create_group(self, claim: Claim, llm=None) -> ClaimGroup:
        from src.agent.conflict import compare_claims  # avoid circular import
        for group in self.claim_groups:
            if group.sub_question_id != claim.sub_question_id:
                continue
            if _jaccard(group.canonical_text, claim.text) > 0.5:
                # Before merging, check for contradiction — similar text can still contradict
                if llm is not None:
                    from src.agent.states import ClaimRelationship
                    self.conflict_candidates_considered += 1
                    self.conflict_llm_checks += 1
                    rel = compare_claims(
                        group.canonical_text, group.scope,
                        claim.text, claim.scope,
                        llm,
                        trace_context={
                            "step": claim.step,
                            "sub_question_id": claim.sub_question_id,
                            "claim_id": claim.id,
                            "existing_group_id": group.id,
                        },
                    )
                    if rel == ClaimRelationship.CONTRADICT:
                        self.conflict_contradictions_found += 1
                        # Don't silently merge — create a separate group and mark both disputed
                        new_group = ClaimGroup(
                            id=_new_id("grp"),
                            canonical_text=claim.text,
                            scope=claim.scope,
                            sub_question_id=claim.sub_question_id,
                            status=GroupStatus.DISPUTED,
                            challenge_status=ChallengeStatus.CHALLENGED_CONFLICT_FOUND,
                        )
                        self.claim_groups.append(new_group)
                        # Provenance: new_group's contradiction comes from existing group's claim
                        existing_rep = group.supporting_claim_ids[0] if group.supporting_claim_ids else group.id
                        if existing_rep not in new_group.contradicting_claim_ids:
                            new_group.contradicting_claim_ids.append(existing_rep)
                        # Provenance: existing group's contradiction is the new claim
                        if claim.id not in group.contradicting_claim_ids:
                            group.contradicting_claim_ids.append(claim.id)
                        group.status = GroupStatus.DISPUTED
                        group.challenge_status = ChallengeStatus.CHALLENGED_CONFLICT_FOUND
                        return new_group
                return group
        group = ClaimGroup(
            id=_new_id("grp"),
            canonical_text=claim.text,
            scope=claim.scope,
            sub_question_id=claim.sub_question_id,
        )
        self.claim_groups.append(group)
        return group

    def _update_group_confidence(self, group: ClaimGroup) -> None:
        domain_count = len(set(group.source_domains))
        group_claim_ids = set(group.supporting_claim_ids)
        has_empirical = any(
            c.claim_type == ClaimType.EMPIRICAL
            for c in self.claims
            if c.id in group_claim_ids
        )
        if domain_count >= 3 and has_empirical:
            group.aggregate_confidence = Confidence.HIGH
            if group.status == GroupStatus.WEAK:
                group.status = GroupStatus.SUPPORTED
        elif domain_count >= 2:
            group.aggregate_confidence = Confidence.MEDIUM
            if group.status == GroupStatus.WEAK:
                group.status = GroupStatus.SUPPORTED
        else:
            group.aggregate_confidence = Confidence.LOW

    def _domain_for_claim(self, claim: Claim) -> Optional[str]:
        for obs in self.observations:
            if obs.id == claim.source_observation_id:
                return obs.domain
        return None

    def _domain_score_for_claim(self, claim: Claim) -> float:
        for obs in self.observations:
            if obs.id == claim.source_observation_id:
                return float(obs.domain_score)
        return 0.0

    def _detect_conflicts(self, new_claim: Claim, new_group: ClaimGroup, llm) -> None:
        from src.agent.conflict import compare_claims  # avoid circular import
        # Compare across ALL groups (not just same sub_question_id) — adversarial sub-questions
        # must be able to challenge supporting claims from other branches.
        # Use lightweight lexical thresholds to gate expensive LLM calls.
        # Recall-first policy: slightly relaxed gates, especially across
        # supporting/adversarial branches where wording can diverge.
        _CROSS_BRANCH_JACCARD = 0.08
        _CROSS_KIND_JACCARD = 0.03
        sq_kind_by_id = {sq.id: sq.kind for sq in self.sub_questions}
        candidate_groups = [
            g for g in self.claim_groups
            if g.id != new_group.id
            and (
                _jaccard(g.canonical_text, new_claim.text) >= _CROSS_BRANCH_JACCARD
                or (
                    sq_kind_by_id.get(g.sub_question_id) != sq_kind_by_id.get(new_claim.sub_question_id)
                    and _jaccard(g.canonical_text, new_claim.text) >= _CROSS_KIND_JACCARD
                )
            )
        ]
        for existing_group in candidate_groups:
            self.conflict_candidates_considered += 1
            if existing_group.scope and new_claim.scope:
                words_a = set(existing_group.scope.lower().split())
                words_b = set(new_claim.scope.lower().split())
                if words_a and words_b and not (words_a & words_b):
                    self.conflict_scope_filtered += 1
                    continue
            self.conflict_llm_checks += 1
            rel = compare_claims(
                existing_group.canonical_text, existing_group.scope,
                new_claim.text, new_claim.scope,
                llm,
                trace_context={
                    "step": new_claim.step,
                    "sub_question_id": new_claim.sub_question_id,
                    "new_claim_id": new_claim.id,
                    "existing_group_id": existing_group.id,
                    "new_group_id": new_group.id,
                },
            )
            if rel == ClaimRelationship.CONTRADICT:
                self.conflict_contradictions_found += 1
                # Provenance: new_group's contradiction comes from existing_group's claim
                existing_rep = existing_group.supporting_claim_ids[0] if existing_group.supporting_claim_ids else existing_group.id
                if existing_rep not in new_group.contradicting_claim_ids:
                    new_group.contradicting_claim_ids.append(existing_rep)
                new_group.status = GroupStatus.DISPUTED
                new_group.challenge_status = ChallengeStatus.CHALLENGED_CONFLICT_FOUND
                # Provenance: existing_group's contradiction is the new claim
                if new_claim.id not in existing_group.contradicting_claim_ids:
                    existing_group.contradicting_claim_ids.append(new_claim.id)
                existing_group.status = GroupStatus.DISPUTED
                existing_group.challenge_status = ChallengeStatus.CHALLENGED_CONFLICT_FOUND
