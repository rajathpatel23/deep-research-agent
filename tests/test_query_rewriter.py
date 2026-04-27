from src.agent.query_rewriter import generate_query_variants
from src.agent.states import SubQuestionKind


class _FakeLLM:
    def __init__(self, response: str):
        self.response = response

    def complete(self, system: str, user: str, trace=None) -> str:
        return self.response


def test_generate_query_variants_parses_json():
    llm = _FakeLLM('{"queries":["cot empirical studies","cot benchmark ablation","cot failures criticisms"]}')
    queries = generate_query_variants(
        "CoT effectiveness question",
        "What evidence supports CoT reasoning gains?",
        SubQuestionKind.SUPPORTING,
        llm,
        step=0,
        max_variants=3,
    )
    assert len(queries) == 3
    assert "empirical" in queries[0]


def test_generate_query_variants_fallback_on_bad_json():
    llm = _FakeLLM("not-json")
    queries = generate_query_variants(
        "Top query",
        "Sub question",
        SubQuestionKind.ADVERSARIAL,
        llm,
        step=0,
        max_variants=3,
    )
    assert queries == []
