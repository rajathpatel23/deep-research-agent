from typing import TYPE_CHECKING, Optional

from src.agent.llm_utils import clean_response
from src.agent.prompt_registry import get_prompt
from src.agent.states import ClaimRelationship

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


def compare_claims(
    text_a: str,
    scope_a: str,
    text_b: str,
    scope_b: str,
    llm: "LLMClient",
    trace_context: Optional[dict] = None,
) -> ClaimRelationship:
    prompt = get_prompt("conflict")
    user = f"Claim A: {text_a} (scope: {scope_a})\nClaim B: {text_b} (scope: {scope_b})"
    trace = {"component": "conflict"}
    if trace_context:
        trace.update(trace_context)
    result = clean_response(llm.complete(prompt["system"], user, trace=trace)).strip().upper()
    try:
        return ClaimRelationship(result)
    except ValueError:
        return ClaimRelationship.COMPATIBLE
