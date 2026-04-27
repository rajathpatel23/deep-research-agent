import json
from src.agent.decomposer import decompose
from src.agent.states import SubQuestionKind
from src.agent.llm import MockProvider, LLMClient
from src.agent.config import load_config


def _mock_llm():
    config = load_config()
    config.mock_mode = True
    return LLMClient(config)


def test_decompose_returns_sub_questions():
    llm = _mock_llm()
    result = decompose("Does RAG improve factual accuracy?", llm)
    assert len(result) > 0


def test_decompose_has_adversarial_sub_question():
    llm = _mock_llm()
    result = decompose("Does RAG improve factual accuracy?", llm)
    kinds = {sq.kind for sq in result}
    assert SubQuestionKind.ADVERSARIAL in kinds


def test_decompose_fallback_on_bad_json():
    """If LLM returns garbage, decomposer falls back to two default sub-questions."""
    class BadProvider:
        def complete(self, system, user, trace=None):
            return "not valid json at all"

    class FakeLLM:
        _provider = BadProvider()
        def complete(self, s, u, trace=None):
            return self._provider.complete(s, u, trace=trace)

    result = decompose("test query", FakeLLM())
    assert len(result) == 2
    kinds = {sq.kind for sq in result}
    assert SubQuestionKind.ADVERSARIAL in kinds
