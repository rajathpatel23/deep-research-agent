import json
from typing import TYPE_CHECKING, List

from src.agent.evidence_store import Claim, Observation, _new_id
from src.agent.llm_utils import extract_json
from src.agent.prompt_registry import get_prompt
from src.agent.states import ClaimType

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


def batch_extract_claims(observations: List[Observation], llm: "LLMClient") -> List[Claim]:
    """Extract claims one observation at a time to stay within Groq TPM limits."""
    if not observations:
        return []
    all_claims = []
    for obs in observations:
        all_claims.extend(_extract_one(obs, llm))
    return all_claims


def _extract_one(obs: Observation, llm: "LLMClient") -> List[Claim]:
    prompt = get_prompt("extractor")
    user = f"[0] Sub-question ID: {obs.sub_question_id}\nSource: {obs.source_url}\nSnippet: {obs.snippet}"
    try:
        raw = llm.complete(
            prompt["system"],
            user,
            trace={
                "step": obs.step,
                "component": "extractor",
                "sub_question_id": obs.sub_question_id,
                "observation_id": obs.id,
                "source_url": obs.source_url,
            },
        )
        items = json.loads(extract_json(raw))
        claims = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if not all(k in item for k in ("source_index", "text", "scope", "claim_type", "verbatim")):
                continue
            text = item.get("text")
            scope = item.get("scope")
            verbatim = item.get("verbatim")
            if not isinstance(text, str) or not text.strip():
                continue
            if not isinstance(scope, str):
                scope = ""
            if not isinstance(verbatim, str):
                verbatim = ""
            try:
                claim_type = ClaimType(item["claim_type"])
            except ValueError:
                claim_type = ClaimType.SPECULATIVE
            claims.append(Claim(
                id=_new_id("clm"),
                text=text,
                scope=scope,
                claim_type=claim_type,
                source_observation_id=obs.id,
                verbatim=verbatim,
                sub_question_id=obs.sub_question_id,
                step=obs.step,
            ))
        return claims
    except (json.JSONDecodeError, KeyError, TypeError, RuntimeError):
        return []


def extract_claims(obs: Observation, llm: "LLMClient") -> List[Claim]:
    """Single-observation extraction (kept for backward compatibility)."""
    return batch_extract_claims([obs], llm)
