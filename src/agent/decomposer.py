import json
from typing import TYPE_CHECKING, List

from src.agent.evidence_store import SubQuestion
from src.agent.llm_utils import extract_json
from src.agent.prompt_registry import get_prompt
from src.agent.states import SubQuestionKind

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


def decompose(query: str, llm: "LLMClient") -> List[SubQuestion]:
    prompt = get_prompt("decomposer")
    raw = llm.complete(
        prompt["system"],
        f"Research query: {query}",
        trace={"step": -1, "component": "decomposer", "query": query},
    )
    try:
        items = json.loads(extract_json(raw))
        return [
            SubQuestion(
                id=item["id"],
                text=item["text"],
                kind=SubQuestionKind(item["kind"]),
            )
            for item in items
            if isinstance(item, dict) and all(k in item for k in ("id", "text", "kind"))
        ]
    except (json.JSONDecodeError, KeyError, ValueError):
        return [
            SubQuestion(id="sq1", text=query, kind=SubQuestionKind.SUPPORTING),
            SubQuestion(id="sq2", text=f"What are the limitations of: {query}", kind=SubQuestionKind.ADVERSARIAL),
        ]
