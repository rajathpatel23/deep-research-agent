from src.agent.extractor import extract_claims
from src.agent.evidence_store import Observation, _new_id
from src.agent.states import ClaimType
from src.agent.config import load_config
from src.agent.llm import LLMClient


def _obs(domain="example.com") -> Observation:
    return Observation(
        id=_new_id("obs"),
        step=0,
        sub_question_id="sq1",
        source_url=f"https://{domain}/article",
        source_title="Test",
        domain=domain,
        snippet="Studies show positive effects in controlled conditions.",
    )


def _mock_llm():
    config = load_config()
    config.mock_mode = True
    return LLMClient(config)


def test_extract_returns_claims():
    llm = _mock_llm()
    claims = extract_claims(_obs(), llm)
    assert len(claims) > 0


def test_extract_claim_has_required_fields():
    llm = _mock_llm()
    claims = extract_claims(_obs(), llm)
    for claim in claims:
        assert claim.text
        assert claim.scope
        assert claim.claim_type in (ClaimType.EMPIRICAL, ClaimType.SPECULATIVE)
        assert claim.verbatim
        assert claim.sub_question_id == "sq1"


def test_extract_claim_type_empirical_or_speculative():
    llm = _mock_llm()
    claims = extract_claims(_obs(), llm)
    types = {c.claim_type for c in claims}
    assert types <= {ClaimType.EMPIRICAL, ClaimType.SPECULATIVE}


def test_extract_fallback_on_bad_json():
    class BadProvider:
        def complete(self, s, u, trace=None):
            return "{{not json}}"

    class FakeLLM:
        def complete(self, s, u, trace=None):
            return BadProvider().complete(s, u, trace=trace)

    claims = extract_claims(_obs(), FakeLLM())
    assert claims == []
