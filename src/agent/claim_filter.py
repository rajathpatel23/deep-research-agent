import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.agent.evidence_store import Claim
from src.agent.llm_utils import extract_json
from src.agent.states import ClaimRelevanceLabel

if TYPE_CHECKING:
    from src.agent.llm import LLMClient


@dataclass
class ClaimRelevanceDecision:
    claim_id: str
    label: str
    reason: str


def filter_claims_for_sub_question(
    top_query: str,
    sub_question_text: str,
    claims: list[Claim],
    llm: "LLMClient",
    step: int,
) -> tuple[list[Claim], list[ClaimRelevanceDecision]]:
    if not claims:
        return [], []

    kept: list[Claim] = []
    decisions: list[ClaimRelevanceDecision] = []
    for claim in claims:
        label, reason = _judge_claim(top_query, sub_question_text, claim, llm, step)
        decisions.append(ClaimRelevanceDecision(claim_id=claim.id, label=label, reason=reason))
        claim.relevance_label = ClaimRelevanceLabel(label)
        if label in {"direct", "adjacent"}:
            kept.append(claim)
    return kept, decisions


def _judge_claim(
    top_query: str,
    sub_question_text: str,
    claim: Claim,
    llm: "LLMClient",
    step: int,
) -> tuple[str, str]:
    system = (
        "You are a strict relevance judge.\n"
        "Classify claim relevance to the sub-question.\n"
        "Return JSON only: {\"label\":\"direct|adjacent|irrelevant\",\"reason\":\"...\"}."
    )
    user = (
        f"Top query: {top_query}\n"
        f"Sub-question: {sub_question_text}\n"
        f"Claim text: {claim.text}\n"
        f"Scope: {claim.scope}\n"
        f"Verbatim: {claim.verbatim}"
    )
    try:
        raw = llm.complete(
            system,
            user,
            trace={
                "step": step,
                "component": "claim_filter",
                "claim_id": claim.id,
                "sub_question_id": claim.sub_question_id,
            },
        )
        payload = json.loads(extract_json(raw))
        label = payload.get("label", "")
        reason = payload.get("reason", "")
        if label not in {"direct", "adjacent", "irrelevant"}:
            return "adjacent", "invalid label fallback"
        if not isinstance(reason, str):
            reason = ""
        return label, reason
    except Exception:
        return "adjacent", "parse fallback"
