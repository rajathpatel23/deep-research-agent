import json
from typing import TYPE_CHECKING

from src.agent.llm_utils import extract_json
from src.agent.states import SubQuestionKind

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


def generate_query_variants(
    top_query: str,
    sub_question_text: str,
    kind: SubQuestionKind,
    llm: "LLMClient",
    step: int,
    max_variants: int = 3,
) -> list[str]:
    system = (
        "You are a retrieval query rewriter for research tasks.\n"
        "Return JSON only: {\"queries\": [\"...\", \"...\", \"...\"]}.\n"
        "Generate diverse, concrete search queries optimized for finding empirical evidence."
    )
    focus = "supporting evidence" if kind == SubQuestionKind.SUPPORTING else "counter-evidence and failures"
    user = (
        f"Top query: {top_query}\n"
        f"Sub-question: {sub_question_text}\n"
        f"Focus: {focus}\n"
        f"Return {max_variants} queries maximum."
    )
    try:
        raw = llm.complete(
            system,
            user,
            trace={
                "step": step,
                "component": "query_rewriter",
                "sub_question_text": sub_question_text,
                "kind": kind.value,
            },
        )
        payload = json.loads(extract_json(raw))
        queries = payload.get("queries", [])
        cleaned = [
            q.strip()
            for q in queries
            if isinstance(q, str) and q.strip()
        ]
        deduped: list[str] = []
        seen = set()
        for q in cleaned:
            if q.lower() not in seen:
                deduped.append(q)
                seen.add(q.lower())
        return deduped[:max_variants]
    except Exception:
        return []
