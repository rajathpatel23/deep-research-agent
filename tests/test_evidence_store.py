import pytest
from src.agent.evidence_store import (
    Claim,
    ClaimGroup,
    EvidenceStore,
    Observation,
    SubQuestion,
    _jaccard,
    _new_id,
)
from src.agent.states import (
    ChallengeStatus,
    ClaimRelationship,
    ClaimRelevanceLabel,
    ClaimType,
    Confidence,
    GroupStatus,
    SubQuestionKind,
)


class _ContradictLLM:
    """Stub LLM that always returns CONTRADICT — used to test conflict paths."""
    def complete(self, system: str, user: str, trace=None) -> str:
        return "CONTRADICT"


class _CompatibleLLM:
    """Stub LLM that always returns COMPATIBLE."""
    def complete(self, system: str, user: str, trace=None) -> str:
        return "COMPATIBLE"


def _obs(step=0, sub_question_id="sq1", domain="example.com", domain_score=0.9) -> Observation:
    return Observation(
        id=_new_id("obs"),
        step=step,
        sub_question_id=sub_question_id,
        source_url=f"https://{domain}/article",
        source_title="Test Article",
        domain=domain,
        snippet="Test snippet.",
        domain_score=domain_score,
    )


def _claim(obs: Observation, text="Some claim about the topic", claim_type=ClaimType.EMPIRICAL) -> Claim:
    return Claim(
        id=_new_id("clm"),
        text=text,
        scope="general conditions",
        claim_type=claim_type,
        source_observation_id=obs.id,
        verbatim="Test verbatim quote.",
        sub_question_id=obs.sub_question_id,
        step=obs.step,
    )


# --- _jaccard ---

def test_jaccard_identical():
    assert _jaccard("the cat sat", "the cat sat") == 1.0


def test_jaccard_disjoint():
    assert _jaccard("alpha beta", "gamma delta") == 0.0


def test_jaccard_partial():
    score = _jaccard("the cat sat on the mat", "the cat")
    assert 0.0 < score < 1.0


def test_jaccard_empty():
    assert _jaccard("", "something") == 0.0


# --- _new_id ---

def test_new_id_prefix():
    assert _new_id("clm").startswith("clm_")


def test_new_id_unique():
    assert _new_id("obs") != _new_id("obs")


# --- EvidenceStore.update ---

def test_update_appends_claims():
    store = EvidenceStore(query="test")
    obs = _obs()
    store.observations.append(obs)
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    claim = _claim(obs)
    store.update([claim])
    assert claim in store.claims


def test_update_creates_claim_group():
    store = EvidenceStore(query="test")
    obs = _obs()
    store.observations.append(obs)
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    store.update([_claim(obs)])
    assert len(store.claim_groups) == 1


def test_update_marks_sub_question_covered():
    store = EvidenceStore(query="test")
    sq = SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING)
    store.sub_questions.append(sq)
    obs = _obs()
    store.observations.append(obs)
    store.update([_claim(obs)])
    assert sq.has_evidence is True


def test_update_stores_adjacent_claims_without_covering():
    store = EvidenceStore(query="test")
    sq = SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING)
    store.sub_questions.append(sq)
    obs = _obs()
    store.observations.append(obs)
    claim = _claim(obs)
    claim.relevance_label = ClaimRelevanceLabel.ADJACENT
    store.update([claim])
    assert len(store.claims) == 0
    assert len(store.adjacent_claims) == 1
    assert store.adjacent_claims[0].id == claim.id
    assert sq.has_evidence is False


def test_low_domain_score_direct_claim_is_downgraded_and_does_not_cover():
    store = EvidenceStore(query="test")
    sq = SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING)
    store.sub_questions.append(sq)
    obs = _obs(domain="noisy.example", domain_score=0.2)
    store.observations.append(obs)
    claim = _claim(obs)
    store.update([claim], min_direct_domain_score=0.6)
    assert len(store.claims) == 0
    assert len(store.adjacent_claims) == 1
    assert store.adjacent_claims[0].relevance_label == ClaimRelevanceLabel.ADJACENT
    assert sq.has_evidence is False


def test_update_groups_similar_claims_together():
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    obs1 = _obs(domain="site1.com")
    obs2 = _obs(domain="site2.com")
    store.observations.extend([obs1, obs2])
    text = "RAG improves factual accuracy in language models significantly"
    store.update([_claim(obs1, text=text), _claim(obs2, text=text)])
    assert len(store.claim_groups) == 1
    assert len(store.claim_groups[0].supporting_claim_ids) == 2


def test_update_separates_dissimilar_claims():
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    obs1 = _obs(domain="site1.com")
    obs2 = _obs(domain="site2.com")
    store.observations.extend([obs1, obs2])
    store.update([
        _claim(obs1, text="RAG improves factual accuracy"),
        _claim(obs2, text="Chain of thought prompting reduces errors in math"),
    ])
    assert len(store.claim_groups) == 2


def test_confidence_low_single_domain():
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    obs = _obs(domain="site1.com")
    store.observations.append(obs)
    store.update([_claim(obs)])
    assert store.claim_groups[0].aggregate_confidence == Confidence.LOW


def test_confidence_medium_two_domains():
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    text = "RAG improves factual accuracy in language models"
    obs1 = _obs(domain="site1.com")
    obs2 = _obs(domain="site2.com")
    store.observations.extend([obs1, obs2])
    store.update([_claim(obs1, text=text), _claim(obs2, text=text)])
    assert store.claim_groups[0].aggregate_confidence == Confidence.MEDIUM


def test_confidence_high_three_empirical_domains():
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    text = "RAG improves factual accuracy in language models significantly"
    obs1 = _obs(domain="a.com")
    obs2 = _obs(domain="b.com")
    obs3 = _obs(domain="c.com")
    store.observations.extend([obs1, obs2, obs3])
    store.update([
        _claim(obs1, text=text, claim_type=ClaimType.EMPIRICAL),
        _claim(obs2, text=text, claim_type=ClaimType.EMPIRICAL),
        _claim(obs3, text=text, claim_type=ClaimType.EMPIRICAL),
    ])
    assert store.claim_groups[0].aggregate_confidence == Confidence.HIGH


# ── conflict detection regression tests ──────────────────────────────────────

def test_same_group_contradiction_creates_separate_group():
    """Similar text that contradicts should split into two groups, both DISPUTED."""
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    obs1 = _obs(domain="site1.com")
    obs2 = _obs(domain="site2.com")
    store.observations.extend([obs1, obs2])
    # Two claims with high Jaccard similarity but contradicting content
    claim1 = _claim(obs1, text="RAG significantly improves factual accuracy in LLMs")
    claim2 = _claim(obs2, text="RAG significantly reduces factual accuracy in LLMs")
    store.update([claim1], llm=_CompatibleLLM())
    store.update([claim2], llm=_ContradictLLM())
    # Should have 2 groups, both DISPUTED
    assert len(store.claim_groups) == 2
    assert all(g.status == GroupStatus.DISPUTED for g in store.claim_groups)


def test_same_group_contradiction_provenance():
    """contradicting_claim_ids must reference the opposing group's claim, not the group's own."""
    store = EvidenceStore(query="test")
    store.sub_questions.append(SubQuestion(id="sq1", text="Q", kind=SubQuestionKind.SUPPORTING))
    obs1 = _obs(domain="site1.com")
    obs2 = _obs(domain="site2.com")
    store.observations.extend([obs1, obs2])
    claim1 = _claim(obs1, text="RAG significantly improves factual accuracy in LLMs")
    claim2 = _claim(obs2, text="RAG significantly reduces factual accuracy in LLMs")
    store.update([claim1], llm=_CompatibleLLM())
    store.update([claim2], llm=_ContradictLLM())
    g1 = store.claim_groups[0]
    g2 = store.claim_groups[1]
    # g1's contradiction must reference a claim from g2, not from g1
    assert all(cid not in g1.supporting_claim_ids for cid in g1.contradicting_claim_ids)
    # g2's contradiction must reference a claim from g1, not from g2
    assert all(cid not in g2.supporting_claim_ids for cid in g2.contradicting_claim_ids)


def test_cross_branch_conflict_detection():
    """Adversarial sub-question claims should be able to dispute supporting claims."""
    store = EvidenceStore(query="test")
    store.sub_questions.extend([
        SubQuestion(id="sq_sup", text="Evidence for RAG", kind=SubQuestionKind.SUPPORTING),
        SubQuestion(id="sq_adv", text="Limitations of RAG", kind=SubQuestionKind.ADVERSARIAL),
    ])
    obs_sup = _obs(sub_question_id="sq_sup", domain="site1.com")
    obs_adv = _obs(sub_question_id="sq_adv", domain="site2.com")
    store.observations.extend([obs_sup, obs_adv])

    def _claim_sq(obs, text, sq_id):
        c = _claim(obs, text=text)
        c.sub_question_id = sq_id
        return c

    claim_sup = _claim_sq(obs_sup, "RAG improves factual accuracy in language models", "sq_sup")
    claim_adv = _claim_sq(obs_adv, "RAG improves factual accuracy in language models", "sq_adv")

    store.update([claim_sup], llm=_CompatibleLLM())
    store.update([claim_adv], llm=_ContradictLLM())

    # Cross-branch conflict: adversarial claim should have disputed the supporting group
    disputed = [g for g in store.claim_groups if g.status == GroupStatus.DISPUTED]
    assert len(disputed) >= 1


def test_cross_kind_low_overlap_still_reaches_conflict_judge():
    """Recall-first gating: supporting/adversarial pairs with low lexical overlap are still checked."""
    store = EvidenceStore(query="test")
    store.sub_questions.extend([
        SubQuestion(id="sq_sup", text="Evidence for CoT", kind=SubQuestionKind.SUPPORTING),
        SubQuestion(id="sq_adv", text="Failures of CoT", kind=SubQuestionKind.ADVERSARIAL),
    ])
    obs_sup = _obs(sub_question_id="sq_sup", domain="site1.com")
    obs_adv = _obs(sub_question_id="sq_adv", domain="site2.com")
    store.observations.extend([obs_sup, obs_adv])

    claim_sup = _claim(obs_sup, text="Chain reasoning improves benchmark performance")
    claim_adv = _claim(obs_adv, text="No improvement seen in reasoning tasks")

    store.update([claim_sup], llm=_CompatibleLLM())
    store.update([claim_adv], llm=_ContradictLLM())

    assert store.conflict_candidates_considered >= 1
    assert store.conflict_llm_checks >= 1
    assert store.conflict_contradictions_found >= 1
    assert any(g.status == GroupStatus.DISPUTED for g in store.claim_groups)


def test_conflict_scope_filter_increments_diagnostics():
    """Scope mismatch should be counted as filtered and avoid an LLM conflict check."""
    store = EvidenceStore(query="test")
    store.sub_questions.extend([
        SubQuestion(id="sq_sup", text="Evidence for method", kind=SubQuestionKind.SUPPORTING),
        SubQuestion(id="sq_adv", text="Limitations of method", kind=SubQuestionKind.ADVERSARIAL),
    ])
    obs_sup = _obs(sub_question_id="sq_sup", domain="site1.com")
    obs_adv = _obs(sub_question_id="sq_adv", domain="site2.com")
    store.observations.extend([obs_sup, obs_adv])

    claim_sup = _claim(obs_sup, text="Method improves performance")
    claim_sup.scope = "math"
    # Keep lexical overlap high enough for cross-branch candidacy but below
    # same-group merge threshold (>0.5), so we exercise scope filtering path.
    claim_adv = _claim(obs_adv, text="Method worsens performance")
    claim_adv.scope = "legal"

    store.update([claim_sup], llm=_CompatibleLLM())
    llm_checks_before = store.conflict_llm_checks
    store.update([claim_adv], llm=_ContradictLLM())

    assert store.conflict_candidates_considered >= 1
    assert store.conflict_scope_filtered >= 1
    # Candidate was filtered by scope in cross-branch detector, so no extra LLM check there.
    assert store.conflict_llm_checks == llm_checks_before
