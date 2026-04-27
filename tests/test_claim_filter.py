from src.agent.claim_filter import filter_claims_for_sub_question
from src.agent.evidence_store import Claim
from src.agent.states import ClaimType


class _FakeLLM:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.idx = 0

    def complete(self, system: str, user: str, trace=None) -> str:
        out = self.responses[min(self.idx, len(self.responses) - 1)]
        self.idx += 1
        return out


def _claims() -> list[Claim]:
    return [
        Claim(
            id="c1",
            text="Directly answers question",
            scope="general",
            claim_type=ClaimType.EMPIRICAL,
            source_observation_id="obs1",
            verbatim="Directly answers question",
            sub_question_id="sq1",
            step=0,
        ),
        Claim(
            id="c2",
            text="Adjacent context only",
            scope="general",
            claim_type=ClaimType.SPECULATIVE,
            source_observation_id="obs2",
            verbatim="Adjacent context only",
            sub_question_id="sq1",
            step=0,
        ),
    ]


def test_claim_filter_keeps_direct_and_adjacent():
    llm = _FakeLLM([
        '{"label":"direct","reason":"answers sub-question"}',
        '{"label":"adjacent","reason":"context only"}',
    ])
    kept, decisions = filter_claims_for_sub_question("q", "sq", _claims(), llm, step=0)
    assert [c.id for c in kept] == ["c1", "c2"]
    assert kept[0].relevance_label == "direct"
    assert kept[1].relevance_label == "adjacent"
    assert len(decisions) == 2


def test_claim_filter_fallback_marks_adjacent():
    llm = _FakeLLM(["not-json", "not-json"])
    kept, decisions = filter_claims_for_sub_question("q", "sq", _claims(), llm, step=0)
    assert [c.id for c in kept] == ["c1", "c2"]
    assert all(d.label == "adjacent" for d in decisions)
