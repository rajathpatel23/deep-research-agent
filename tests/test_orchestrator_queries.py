import json

from src.agent.config import Config, LLMProvider, SearchBackend
from src.agent.evidence_store import Claim, ClaimGroup, SubQuestion
from src.agent.orchestrator import (
    _build_challenge_query,
    _build_search_query,
    _should_use_research_mode,
    run,
)
from src.agent.retriever import SearchResult
from src.agent.states import ClaimRelevanceLabel, ClaimType, SubQuestionKind


def test_build_search_query_includes_original_query_context():
    sq = SubQuestion(
        id="sq1",
        text="What evidence supports chain-of-thought generalization?",
        kind=SubQuestionKind.SUPPORTING,
    )
    query = "Do chain-of-thought models generalize under distribution shift?"
    built = _build_search_query(query, sq)
    assert "chain-of-thought" in built.lower()
    assert "distribution shift" in built.lower()
    assert "evidence supports" in built.lower()


def test_build_search_query_adds_adversarial_terms():
    sq = SubQuestion(
        id="sq2",
        text="When does chain-of-thought fail under distribution shift?",
        kind=SubQuestionKind.ADVERSARIAL,
    )
    built = _build_search_query(
        "Do chain-of-thought models generalize under distribution shift?",
        sq,
    )
    assert "limitations" in built.lower()
    assert "criticisms" in built.lower()
    assert "contradictory evidence" in built.lower()


def test_supporting_evidence_queries_use_research_mode():
    sq = SubQuestion(
        id="sq1",
        text="What empirical evidence supports chain-of-thought generalization?",
        kind=SubQuestionKind.SUPPORTING,
    )
    assert _should_use_research_mode(sq) is True


def test_adversarial_queries_do_not_use_research_mode():
    sq = SubQuestion(
        id="sq2",
        text="What are the limitations of chain-of-thought under distribution shift?",
        kind=SubQuestionKind.ADVERSARIAL,
    )
    assert _should_use_research_mode(sq) is False


def test_build_challenge_query_keeps_original_topic():
    group = ClaimGroup(
        id="grp1",
        canonical_text="Chain-of-thought improves accuracy under distribution shift",
        scope="reasoning benchmarks",
        sub_question_id="sq1",
    )
    built = _build_challenge_query(
        "Do chain-of-thought models generalize under distribution shift?",
        group,
        step=1,
    )
    assert "chain-of-thought" in built.lower()
    assert "distribution shift" in built.lower()
    assert any(term in built.lower() for term in ("limitations", "criticism", "not hold"))


def test_run_propagates_domain_score_and_applies_direct_gating(tmp_path, monkeypatch):
    sq = SubQuestion(id="sq1", text="What empirical evidence supports chain-of-thought?", kind=SubQuestionKind.SUPPORTING)
    cached_results = {
        "sq1": [
            SearchResult(
                url="https://noisy.example/article",
                title="Noisy source",
                snippet="This source claims a large effect under limited conditions." * 3,
                domain="noisy.example",
                domain_score=0.2,
            )
        ]
    }

    def _fake_extract_claims(new_obs, llm, parallelism=1):
        obs = new_obs[0]
        return [
            Claim(
                id="clm_test",
                text="Chain-of-thought improves outcomes in this setup.",
                scope="limited setup",
                claim_type=ClaimType.EMPIRICAL,
                source_observation_id=obs.id,
                verbatim="improves outcomes",
                sub_question_id=obs.sub_question_id,
                step=obs.step,
                relevance_label=ClaimRelevanceLabel.DIRECT,
            )
        ]

    monkeypatch.setattr("src.agent.orchestrator.batch_extract_claims", _fake_extract_claims)

    cfg = Config(
        llm_provider=LLMProvider.MOCK,
        llm_model="mock",
        search_backend=SearchBackend.MOCK,
        groq_api_key=None,
        anthropic_api_key=None,
        nebius_api_key=None,
        minimax_api_key=None,
        tavily_api_key=None,
        mock_mode=True,
        enable_claim_filter=False,
        min_direct_domain_score=0.6,
    )

    run(
        query="Is chain-of-thought effective?",
        mode="baseline",
        max_steps=1,
        output_dir=tmp_path,
        config=cfg,
        shared_sub_questions=[sq],
        observation_cache=cached_results,
    )

    store = json.loads((tmp_path / "evidence_store.json").read_text())
    assert store["observations"][0]["domain_score"] == 0.2
    assert store["sub_questions"][0]["has_evidence"] is False
    assert len(store["claims"]) == 0
    assert len(store["adjacent_claims"]) == 1
