from src.agent.evidence_store import SubQuestion
from src.agent.states import SubQuestionKind
from experiment import _build_prefetch_cache


class _FakeRetriever:
    def __init__(self):
        self.calls = []

    def search(self, query: str, max_results: int, research_mode: bool):
        self.calls.append(
            {"query": query, "max_results": max_results, "research_mode": research_mode}
        )
        if "limitations" in query.lower():
            return []
        return [{"url": "https://example.com"}]


def test_prefetch_cache_only_stores_non_empty_results():
    retriever = _FakeRetriever()
    sqs = [
        SubQuestion(
            id="sq1",
            text="What empirical studies support chain-of-thought?",
            kind=SubQuestionKind.SUPPORTING,
        ),
        SubQuestion(
            id="sq2",
            text="What are the limitations of chain-of-thought?",
            kind=SubQuestionKind.ADVERSARIAL,
        ),
    ]

    cache = _build_prefetch_cache(
        "Is chain-of-thought effective overall?",
        sqs,
        retriever,
        max_results=3,
    )

    assert "sq1" in cache
    assert "sq2" not in cache
    assert len(retriever.calls) == 2
    assert retriever.calls[0]["research_mode"] is True
    assert retriever.calls[1]["research_mode"] is False
