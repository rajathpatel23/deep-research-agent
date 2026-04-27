from src.agent.reranker import rerank_results
from src.agent.retriever import SearchResult


class _FakeLLM:
    def __init__(self, response: str):
        self.response = response

    def complete(self, system: str, user: str, trace=None) -> str:
        return self.response


def _results() -> list[SearchResult]:
    return [
        SearchResult(url="https://a.com", title="A", snippet="about topic", domain="a.com", domain_score=0.5),
        SearchResult(url="https://b.com", title="B", snippet="very relevant topic evidence", domain="b.com", domain_score=0.5),
        SearchResult(url="https://c.com", title="C", snippet="loosely related", domain="c.com", domain_score=0.5),
    ]


def test_reranker_keeps_high_score_results():
    llm = _FakeLLM(
        '{"decisions":['
        '{"index":0,"score":1,"reason":"weak"},'
        '{"index":1,"score":3,"reason":"strong"},'
        '{"index":2,"score":2,"reason":"good"}'
        "]}",
    )
    kept, decisions = rerank_results("q", "sq", _results(), llm, step=0, top_k=2)
    assert len(kept) == 2
    assert {r.url for r in kept} == {"https://b.com", "https://c.com"}
    assert len(decisions) == 3


def test_reranker_fallback_when_invalid_response():
    llm = _FakeLLM("not-json")
    kept, decisions = rerank_results("q", "sq", _results(), llm, step=0, top_k=2)
    assert len(kept) == 2
    assert len(decisions) == 3
