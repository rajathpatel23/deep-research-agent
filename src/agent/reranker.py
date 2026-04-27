import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.agent.llm_utils import extract_json
from src.agent.retriever import SearchResult

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


@dataclass
class RerankDecision:
    index: int
    score: int
    keep: bool
    reason: str


def rerank_results(
    top_query: str,
    sub_question_text: str,
    results: list[SearchResult],
    llm: "LLMClient",
    step: int,
    top_k: int = 4,
) -> tuple[list[SearchResult], list[RerankDecision]]:
    if len(results) <= 1:
        decisions = [RerankDecision(index=i, score=3, keep=True, reason="single result") for i, _ in enumerate(results)]
        return results, decisions

    packed = []
    for i, r in enumerate(results):
        packed.append(
            {
                "index": i,
                "title": r.title,
                "domain": r.domain,
                "url": r.url,
                "snippet": r.snippet[:500],
            }
        )

    system = (
        "You are a result reranker for research retrieval.\n"
        "Return JSON only: {\"decisions\":[{\"index\":0,\"score\":0-3,\"reason\":\"...\"}]}\n"
        "Score strict relevance to the sub-question (3=highly relevant, 0=irrelevant)."
    )
    user = (
        f"Top query: {top_query}\n"
        f"Sub-question: {sub_question_text}\n"
        f"Results JSON:\n{json.dumps(packed)}"
    )
    try:
        raw = llm.complete(
            system,
            user,
            trace={
                "step": step,
                "component": "reranker",
                "candidate_count": len(results),
                "sub_question_text": sub_question_text,
            },
        )
        payload = json.loads(extract_json(raw))
        items = payload.get("decisions", [])
        decisions: list[RerankDecision] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            idx = item.get("index")
            score = item.get("score")
            reason = item.get("reason", "")
            if not isinstance(idx, int) or idx < 0 or idx >= len(results):
                continue
            if not isinstance(score, int):
                continue
            score = max(0, min(3, score))
            decisions.append(
                RerankDecision(
                    index=idx,
                    score=score,
                    keep=score >= 2,
                    reason=reason if isinstance(reason, str) else "",
                )
            )
        if not decisions:
            raise ValueError("No valid rerank decisions")
        by_score = sorted(decisions, key=lambda d: (d.score, -d.index), reverse=True)
        kept = [d for d in by_score if d.keep][:top_k]
        if not kept:
            kept = by_score[: min(2, len(by_score))]
        keep_idx = {d.index for d in kept}
        kept_results = [r for i, r in enumerate(results) if i in keep_idx]
        # Normalize decision list to include all indices for tracing consistency.
        full_decisions = []
        decision_map = {d.index: d for d in decisions}
        for i in range(len(results)):
            if i in decision_map:
                full_decisions.append(decision_map[i])
            else:
                full_decisions.append(RerankDecision(index=i, score=0, keep=False, reason="not scored"))
        return kept_results, full_decisions
    except Exception:
        fallback = results[:top_k]
        decisions = [
            RerankDecision(index=i, score=(3 if i < top_k else 1), keep=(i < top_k), reason="fallback")
            for i, _ in enumerate(results)
        ]
        return fallback, decisions
