import copy
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Optional

from src.agent.config import Config, load_config
from src.agent.decomposer import decompose
from src.agent.evaluator import classify_step
from src.agent.evidence_store import EvidenceStore, LLMCallRecord, Observation, StepRecord, _new_id
from src.agent.claim_filter import filter_claims_for_sub_question
from src.agent.extractor import batch_extract_claims
from src.agent.llm import LLMClient
from src.agent.planner import (
    ChallengeAction,
    SearchAction,
    StopAction,
    baseline_plan,
    guided_plan,
)
from src.agent.prompt_registry import reset_session, session_versions
from src.agent.dashboard import generate_dashboard
from src.agent.metrics import compute_metrics
from src.agent.query_rewriter import generate_query_variants
from src.agent.report import generate_report
from src.agent.reranker import rerank_results
from src.agent.retriever import Retriever
from src.agent.states import ChallengeStatus, SubQuestionKind, TerminationReason


def _print_store_state(store) -> None:
    covered = sum(1 for sq in store.sub_questions if sq.has_evidence)
    print(f"  [store] sub-questions: {covered}/{len(store.sub_questions)} covered  |  "
          f"claim groups: {len(store.claim_groups)}  |  "
          f"disputes: {sum(1 for g in store.claim_groups if g.status.value == 'disputed')}")
    for g in store.claim_groups[-3:]:
        print(f"    group [{g.aggregate_confidence.value}] {g.canonical_text[:80]}")


_RESEARCH_HINTS = (
    "evidence",
    "empirical",
    "study",
    "studies",
    "experiment",
    "experiments",
    "paper",
    "papers",
    "benchmark",
    "benchmarks",
)


def _normalize_query_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split()).strip().rstrip("?")


def _build_search_query(query: str, sq) -> str:
    topic = _normalize_query_text(query)
    focus = _normalize_query_text(sq.text)
    if sq.kind == SubQuestionKind.ADVERSARIAL:
        return (
            f"{topic} {focus} limitations criticisms failures negative results no improvement "
            "replication failure contradictory evidence"
        )
    return f"{topic} {focus}"


def _recent_search_queries(store: EvidenceStore, limit: int = 6) -> set[str]:
    """Return normalized base search queries from recent search steps."""
    if limit <= 0:
        return set()
    sq_by_id = {sq.id: sq for sq in store.sub_questions}
    recent = []
    for record in reversed(store.step_history):
        if not record.action.startswith("search:"):
            continue
        sq_id = record.action.split(":", 1)[1].strip()
        sq = sq_by_id.get(sq_id)
        if sq is None:
            continue
        recent.append(_normalize_query_text(_build_search_query(store.query, sq)))
        if len(recent) >= limit:
            break
    return set(recent)


def _enforce_query_novelty(
    store: EvidenceStore,
    sq,
    search_query: str,
    sq_failure_streak: int,
    recent_window: int = 6,
) -> tuple[str, bool]:
    """Avoid repeating identical base queries across recent steps."""
    normalized = _normalize_query_text(search_query)
    recent = _recent_search_queries(store, limit=recent_window)
    if normalized not in recent:
        return search_query, False
    novelty_pivots = _pivot_queries(store.query, sq, max(1, sq_failure_streak + 1))
    for candidate in novelty_pivots:
        if _normalize_query_text(candidate) not in recent:
            return candidate, True
    forced = f"{search_query} replication benchmark ablation"
    return forced, True


def _preview_text(text: str, max_chars: int = 140) -> str:
    clean = _normalize_query_text(text)
    if len(clean) <= max_chars:
        return clean
    if max_chars <= 12:
        return clean[:max_chars]
    keep = (max_chars - 3) // 2
    return f"{clean[:keep]}...{clean[-keep:]}"


def _build_challenge_query(query: str, group, step: int) -> str:
    topic = _normalize_query_text(query)
    claim = _normalize_query_text(group.canonical_text)
    scope = _normalize_query_text(group.scope) if group.scope else ""
    scope_part = f" {scope}" if scope else ""
    templates = [
        f"{topic} {claim}{scope_part} limitations failures",
        f"{topic} {claim}{scope_part} criticism contradictory evidence",
        f"{topic} when does {claim}{scope_part} not hold",
    ]
    return templates[step % len(templates)]


def _should_use_research_mode(sq) -> bool:
    if sq.kind != SubQuestionKind.SUPPORTING:
        return False
    text = sq.text.lower()
    return any(hint in text for hint in _RESEARCH_HINTS)


def _dedupe_results(results):
    seen = set()
    deduped = []
    for r in results:
        if r.url in seen:
            continue
        seen.add(r.url)
        deduped.append(r)
    return deduped


def _filter_recent_urls_for_sub_question(
    store: EvidenceStore,
    sub_question_id: str,
    results,
    recent_steps: int = 4,
):
    """Drop URLs seen recently for the same sub-question to force novelty."""
    if not results:
        return results
    min_step = 0
    if store.step_history:
        max_step = max((r.step for r in store.step_history), default=0)
        min_step = max(0, max_step - recent_steps + 1)
    recent_urls = {
        obs.source_url
        for obs in store.observations
        if obs.sub_question_id == sub_question_id and obs.step >= min_step
    }
    return [r for r in results if r.url not in recent_urls]


def _rewrite_sub_question(query: str, sq_text: str, llm: LLMClient, step: int) -> str:
    system = (
        "You rewrite research sub-questions for web search recall.\n"
        "Return exactly one rewritten question in plain text.\n"
        "Keep it specific and include concrete keywords (task, metrics, failures, benchmarks).\n"
        "Do not add bullets, quotes, or explanations."
    )
    user = (
        f"Top-level query: {query}\n"
        f"Current sub-question: {sq_text}\n"
        "Rewrite to maximize discoverability of empirical sources."
    )
    rewritten = llm.complete(
        system,
        user,
        trace={"step": step, "component": "recovery", "recovery_type": "rewrite_sub_question"},
    ).strip()
    if not rewritten:
        return sq_text
    rewritten = rewritten.splitlines()[0].strip().strip('"').strip("'")
    return rewritten or sq_text


def _recent_sq_failure_streak(store: EvidenceStore, sub_question_id: str) -> int:
    """Count consecutive non-progress outcomes for the same sub-question."""
    streak = 0
    failure_results = {"NO_EXTRACTABLE_CLAIMS", "NO_RETRIEVAL_RESULTS", "DEAD_END"}
    for record in reversed(store.step_history):
        if record.sub_question_id != sub_question_id:
            continue
        if record.result.value in failure_results:
            streak += 1
            continue
        break
    return streak


def _pivot_queries(query: str, sq, failure_streak: int) -> list[str]:
    """Generate progressively stricter retrieval pivots for hard sub-questions."""
    if failure_streak <= 0:
        return []
    topic = _normalize_query_text(query)
    focus = _normalize_query_text(sq.text)
    pivots: list[str] = []
    # Tier A: simplify and focus on measurable outcomes.
    pivots.append(f"{topic} {focus} empirical benchmark accuracy f1")
    # Tier B: enforce comparator/evaluation language.
    if failure_streak >= 1:
        pivots.append(
            f"{topic} {focus} ablation controlled comparison statistically significant results"
        )
    # Tier C: force paper-oriented retrieval after repeated failures.
    if failure_streak >= 2:
        pivots.append(f"{topic} {focus} arxiv openreview acl findings pdf")
    # Tier D: hard domain constraints if still stuck.
    if failure_streak >= 3:
        pivots.append(f"{focus} site:arxiv.org")
        pivots.append(f"{focus} site:openreview.net")
    return pivots


def _search_query_variants(
    retriever: Retriever,
    query_variants: list[str],
    max_results: int,
    research_mode: bool,
    parallelism: int,
    adaptive_parallelism: bool,
):
    if not query_variants:
        return []
    effective_parallelism = (
        retriever.suggest_parallelism(parallelism) if adaptive_parallelism else parallelism
    )
    if effective_parallelism <= 1 or len(query_variants) <= 1:
        raw_results = []
        for qv in query_variants:
            raw_results.extend(
                retriever.search(
                    qv,
                    max_results=max_results,
                    research_mode=research_mode,
                )
            )
        return raw_results

    raw_results_by_idx: dict[int, list] = {}
    max_workers = min(effective_parallelism, len(query_variants))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                retriever.search,
                qv,
                max_results=max_results,
                research_mode=research_mode,
            ): idx
            for idx, qv in enumerate(query_variants)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            raw_results_by_idx[idx] = future.result()

    merged = []
    for idx in range(len(query_variants)):
        merged.extend(raw_results_by_idx.get(idx, []))
    return merged


def run(
    query: str,
    mode: str,
    max_steps: int,
    output_dir: Path,
    config: Optional[Config] = None,
    verbose: bool = False,
    shared_sub_questions: Optional[list] = None,
    observation_cache: Optional[Dict] = None,
) -> Dict:
    reset_session()

    if config is None:
        config = load_config()
    config.max_steps = max_steps

    llm = LLMClient(config)
    retriever = Retriever(config)

    store = EvidenceStore(query=query)
    if shared_sub_questions is not None:
        # Deep copy so has_evidence flags start fresh for each run
        store.sub_questions = [sq.model_copy(deep=True) for sq in shared_sub_questions]
        print(f"[decompose] {len(store.sub_questions)} sub-questions (shared)")
    else:
        store.sub_questions = decompose(query, llm)
        print(f"[decompose] {len(store.sub_questions)} sub-questions")
    for sq in store.sub_questions:
        print(f"  [{sq.kind.value}] {sq.text}")

    output_dir.mkdir(parents=True, exist_ok=True)
    sub_question_id = ""

    for step in range(max_steps):
        query_prep_event_start = retriever.get_query_prep_event_count()
        action = (
            baseline_plan(store, step)
            if mode == "baseline"
            else guided_plan(
                store,
                step,
                max_steps,
                diminishing_window=config.diminishing_window,
                min_coverage_for_diminishing=config.min_coverage_for_diminishing,
            )
        )

        if isinstance(action, StopAction):
            store.termination_reason = action.reason.value
            print(f"[stop] step={step} reason={action.reason.value}")
            break

        claims_before = {c.id for c in store.claims}
        groups_before = {g.id: g.model_copy(deep=True) for g in store.claim_groups}
        retrieved_results = 0
        observations_added = 0
        extracted_claims = 0
        query_variants_tried = 0
        rerank_in_count = 0
        rerank_out_count = 0
        claims_filtered_out = 0
        adjacent_claims_added = 0
        direct_claims_added = 0
        direct_claim_conversion_rate = 0.0
        query_compression_attempts = 0
        query_compression_llm_successes = 0
        query_compression_fallback_truncations = 0
        query_compression_chars_saved = 0

        if isinstance(action, SearchAction):
            sq = next((s for s in store.sub_questions if s.id == action.sub_question_id), None)
            if sq is None:
                continue
            search_query = _build_search_query(query, sq)
            sq_failure_streak = _recent_sq_failure_streak(store, sq.id)
            search_query, was_novelty_rewritten = _enforce_query_novelty(
                store,
                sq,
                search_query,
                sq_failure_streak,
            )
            query_variants = [search_query]
            query_variants.extend(_pivot_queries(query, sq, sq_failure_streak))
            # Escalate to high-quality research domains after repeated extraction dead-zones.
            research_mode = (
                config.research_mode
                and (_should_use_research_mode(sq) or sq_failure_streak >= 2)
            )
            print(f"[step {step}] search[{sq.id}] focus: {_preview_text(sq.text, max_chars=90)}")
            print(f"  query: {_preview_text(search_query)}")
            if was_novelty_rewritten:
                print("  [novelty] base query repeated recently; using pivoted query")
            if observation_cache is not None and sq.id in observation_cache:
                results = observation_cache[sq.id]
                print(f"  [cached] {len(results)} results")
            else:
                rewritten_variants = generate_query_variants(
                    query,
                    sq.text,
                    sq.kind,
                    llm,
                    step=step,
                    max_variants=config.query_rewrite_variants,
                )
                query_variants.extend(rewritten_variants)
                deduped_queries = []
                seen_queries = set()
                for q in query_variants:
                    qn = q.strip()
                    key = qn.lower()
                    if not qn or key in seen_queries:
                        continue
                    deduped_queries.append(qn)
                    seen_queries.add(key)
                query_variants = deduped_queries
                query_variants_tried = len(query_variants)
                raw_results = _search_query_variants(
                    retriever,
                    query_variants,
                    max_results=config.max_results,
                    research_mode=research_mode,
                    parallelism=config.search_parallelism,
                    adaptive_parallelism=config.adaptive_parallelism,
                )
                raw_results = _dedupe_results(raw_results)
                rerank_in_count = len(raw_results)
                results, _ = rerank_results(
                    query,
                    sq.text,
                    raw_results,
                    llm,
                    step=step,
                    top_k=config.rerank_top_k,
                )
                rerank_out_count = len(results)
            novelty_filtered = _filter_recent_urls_for_sub_question(store, sq.id, results)
            if len(novelty_filtered) != len(results):
                print(f"  [novelty] removed {len(results) - len(novelty_filtered)} repeated URLs")
            results = novelty_filtered
            recovery_attempts = 0
            recovery_strategy = ""
            if not results and config.enable_recovery:
                # Recovery 1: expand domain constraints (turn off research whitelist).
                if research_mode and recovery_attempts < config.recovery_max_attempts:
                    recovery_attempts += 1
                    recovery_strategy = "expand_domain"
                    raw_results = _search_query_variants(
                        retriever,
                        query_variants,
                        max_results=config.max_results,
                        research_mode=False,
                        parallelism=config.search_parallelism,
                        adaptive_parallelism=config.adaptive_parallelism,
                    )
                    raw_results = _dedupe_results(raw_results)
                    rerank_in_count = len(raw_results)
                    results, _ = rerank_results(
                        query,
                        sq.text,
                        raw_results,
                        llm,
                        step=step,
                        top_k=config.rerank_top_k,
                    )
                    rerank_out_count = len(results)
                # Recovery 2: rewrite sub-question for better retrieval recall.
                if not results and recovery_attempts < config.recovery_max_attempts:
                    recovery_attempts += 1
                    recovery_strategy = (
                        "expand_domain+rewrite_sub_question"
                        if recovery_strategy
                        else "rewrite_sub_question"
                    )
                    rewritten_sq_text = _rewrite_sub_question(query, sq.text, llm, step)
                    if rewritten_sq_text != sq.text:
                        sq.text = rewritten_sq_text
                    rewritten_query = _build_search_query(query, sq)
                    rewrite_variants = [rewritten_query]
                    rewrite_variants.extend(_pivot_queries(query, sq, sq_failure_streak + 1))
                    rewrite_variants.extend(
                        generate_query_variants(
                            query,
                            sq.text,
                            sq.kind,
                            llm,
                            step=step,
                            max_variants=config.query_rewrite_variants,
                        )
                    )
                    rewrite_variants = list(dict.fromkeys(q.strip() for q in rewrite_variants if q.strip()))
                    query_variants_tried += len(rewrite_variants)
                    print(f"  [recovery] rewritten search: {_preview_text(rewritten_query)}")
                    raw_results = _search_query_variants(
                        retriever,
                        rewrite_variants,
                        max_results=config.max_results,
                        research_mode=False,
                        parallelism=config.search_parallelism,
                        adaptive_parallelism=config.adaptive_parallelism,
                    )
                    raw_results = _dedupe_results(raw_results)
                    rerank_in_count = len(raw_results)
                    results, _ = rerank_results(
                        query,
                        sq.text,
                        raw_results,
                        llm,
                        step=step,
                        top_k=config.rerank_top_k,
                    )
                    rerank_out_count = len(results)
            retrieved_results = len(results)
            if verbose:
                for r in results:
                    print(f"  source: {r.domain}  {r.url}")
                    print(f"    {r.snippet[:120]}")
            new_obs = [
                Observation(
                    id=_new_id("obs"), step=step, sub_question_id=sq.id,
                    source_url=r.url, source_title=r.title, domain=r.domain, snippet=r.snippet,
                    domain_score=r.domain_score,
                )
                for r in results
            ]
            store.observations.extend(new_obs)
            observations_added = len(new_obs)
            new_claims = batch_extract_claims(
                new_obs,
                llm,
                parallelism=config.extract_parallelism,
            )
            if config.enable_claim_filter:
                filtered_claims, _ = filter_claims_for_sub_question(
                    query,
                    sq.text,
                    new_claims,
                    llm,
                    step=step,
                )
                claims_filtered_out = len(new_claims) - len(filtered_claims)
                new_claims = filtered_claims
            # Recovery 3: results existed but were not extractable; force one rescue pivot.
            if (
                not new_claims
                and results
                and config.enable_recovery
                and recovery_attempts < config.recovery_max_attempts
            ):
                recovery_attempts += 1
                recovery_strategy = (
                    f"{recovery_strategy}+extractor_rescue_pivot"
                    if recovery_strategy
                    else "extractor_rescue_pivot"
                )
                rescue_variants = _pivot_queries(query, sq, sq_failure_streak + 2)
                rescue_variants = [q.strip() for q in rescue_variants if q.strip()]
                if rescue_variants:
                    query_variants_tried += len(rescue_variants)
                    rescue_raw = _search_query_variants(
                        retriever,
                        rescue_variants,
                        max_results=config.max_results,
                        research_mode=True,
                        parallelism=config.search_parallelism,
                        adaptive_parallelism=config.adaptive_parallelism,
                    )
                    rescue_raw = _dedupe_results(rescue_raw)
                    rerank_in_count += len(rescue_raw)
                    rescue_results, _ = rerank_results(
                        query,
                        sq.text,
                        rescue_raw,
                        llm,
                        step=step,
                        top_k=config.rerank_top_k,
                    )
                    rerank_out_count += len(rescue_results)
                    rescue_obs = [
                        Observation(
                            id=_new_id("obs"), step=step, sub_question_id=sq.id,
                            source_url=r.url, source_title=r.title, domain=r.domain, snippet=r.snippet,
                            domain_score=r.domain_score,
                        )
                        for r in rescue_results
                    ]
                    store.observations.extend(rescue_obs)
                    observations_added += len(rescue_obs)
                    rescue_claims = batch_extract_claims(
                        rescue_obs,
                        llm,
                        parallelism=config.extract_parallelism,
                    )
                    if config.enable_claim_filter:
                        filtered_claims, _ = filter_claims_for_sub_question(
                            query,
                            sq.text,
                            rescue_claims,
                            llm,
                            step=step,
                        )
                        claims_filtered_out += len(rescue_claims) - len(filtered_claims)
                        rescue_claims = filtered_claims
                    new_claims.extend(rescue_claims)
            store.update(new_claims, llm, min_direct_domain_score=config.min_direct_domain_score)
            extracted_claims = len(new_claims)
            adjacent_claims_added = sum(1 for c in new_claims if c.relevance_label.value == "adjacent")
            direct_claims_added = extracted_claims - adjacent_claims_added
            direct_claim_conversion_rate = (
                round(direct_claims_added / extracted_claims, 3) if extracted_claims else 0.0
            )
            print(f"  → {len(new_claims)} claims extracted")
            if verbose:
                for c in new_claims:
                    print(f"    [{c.claim_type.value}] {c.text[:100]}  (scope: {c.scope})")
            sub_question_id = sq.id

        elif isinstance(action, ChallengeAction):
            group = next((g for g in store.claim_groups if g.id == action.claim_group_id), None)
            if group is None:
                continue
            challenge_query = _build_challenge_query(query, group, step)
            print(f"[step {step}] challenge[{group.id}]: {_preview_text(challenge_query, max_chars=120)}")
            results = retriever.search(
                challenge_query,
                max_results=config.max_results,
                research_mode=False,
            )
            retrieved_results = len(results)
            if verbose:
                for r in results:
                    print(f"  source: {r.domain}  {r.url}")
                    print(f"    {r.snippet[:120]}")
            new_obs = [
                Observation(
                    id=_new_id("obs"), step=step, sub_question_id=group.sub_question_id,
                    source_url=r.url, source_title=r.title, domain=r.domain, snippet=r.snippet,
                    domain_score=r.domain_score,
                )
                for r in results
            ]
            store.observations.extend(new_obs)
            observations_added = len(new_obs)
            new_claims = batch_extract_claims(
                new_obs,
                llm,
                parallelism=config.extract_parallelism,
            )
            if config.enable_claim_filter:
                challenge_sq = next((s for s in store.sub_questions if s.id == group.sub_question_id), None)
                sq_text = challenge_sq.text if challenge_sq is not None else group.canonical_text
                filtered_claims, _ = filter_claims_for_sub_question(
                    query,
                    sq_text,
                    new_claims,
                    llm,
                    step=step,
                )
                claims_filtered_out = len(new_claims) - len(filtered_claims)
                new_claims = filtered_claims
            store.update(new_claims, llm, min_direct_domain_score=config.min_direct_domain_score)
            extracted_claims = len(new_claims)
            adjacent_claims_added = sum(1 for c in new_claims if c.relevance_label.value == "adjacent")
            direct_claims_added = extracted_claims - adjacent_claims_added
            direct_claim_conversion_rate = (
                round(direct_claims_added / extracted_claims, 3) if extracted_claims else 0.0
            )
            if group.challenge_status == ChallengeStatus.UNCHALLENGED:
                group.challenge_status = ChallengeStatus.CHALLENGED_NO_CONFLICT
            print(f"  → {len(new_claims)} claims extracted")
            if verbose:
                for c in new_claims:
                    print(f"    [{c.claim_type.value}] {c.text[:100]}  (scope: {c.scope})")
            sub_question_id = group.sub_question_id

        claims_after = {c.id for c in store.claims}
        groups_after = {g.id: g for g in store.claim_groups}
        result = classify_step(
            claims_before,
            claims_after,
            groups_before,
            groups_after,
            retrieved_results=retrieved_results,
            extracted_claims=extracted_claims,
        )
        result_reason = ""
        if result.value == "NO_RETRIEVAL_RESULTS":
            result_reason = "Retriever returned zero usable results."
        elif result.value == "NO_EXTRACTABLE_CLAIMS":
            result_reason = "Results existed, but extractor produced zero claims."

        action_tag = getattr(action, "sub_question_id", "") or getattr(action, "claim_group_id", "")
        step_query_prep_events = retriever.get_query_prep_events_since(query_prep_event_start)
        query_compression_attempts = sum(1 for e in step_query_prep_events if e.get("compression_attempted"))
        query_compression_llm_successes = sum(1 for e in step_query_prep_events if e.get("compression_method") == "llm")
        query_compression_fallback_truncations = sum(1 for e in step_query_prep_events if e.get("compression_fallback_used"))
        query_compression_chars_saved = sum(int(e.get("compression_saved_chars", 0)) for e in step_query_prep_events)
        store.step_history.append(StepRecord(
            step=step,
            action=f"{action.type.value}:{action_tag}",
            sub_question_id=sub_question_id,
            result=result,
            retrieved_results=retrieved_results,
            observations_added=observations_added,
            extracted_claims=extracted_claims,
            result_reason=result_reason,
            recovery_attempts=recovery_attempts if isinstance(action, SearchAction) else 0,
            recovery_strategy=recovery_strategy if isinstance(action, SearchAction) else "",
            query_variants_tried=query_variants_tried,
            rerank_in_count=rerank_in_count,
            rerank_out_count=rerank_out_count,
            claims_filtered_out=claims_filtered_out,
            adjacent_claims_added=adjacent_claims_added,
            direct_claims_added=direct_claims_added,
            direct_claim_conversion_rate=direct_claim_conversion_rate,
            query_compression_attempts=query_compression_attempts,
            query_compression_llm_successes=query_compression_llm_successes,
            query_compression_fallback_truncations=query_compression_fallback_truncations,
            query_compression_chars_saved=query_compression_chars_saved,
        ))
        print(f"  → classified: {result.value}")
        if verbose:
            _print_store_state(store)
        (output_dir / "evidence_store.json").write_text(
            json.dumps(store.model_dump(), indent=2)
        )

    if store.termination_reason is None:
        store.termination_reason = TerminationReason.BUDGET_EXHAUSTED.value

    print("[report] generating...")
    report_text = generate_report(store, llm)
    store.llm_calls = [LLMCallRecord.model_validate(item) for item in llm.get_trace()]

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.md").write_text(report_text)
    (output_dir / "evidence_store.json").write_text(
        json.dumps(store.model_dump(), indent=2)
    )

    metrics = compute_metrics(store, report_text)
    conflict_diagnostics = {
        "candidates_considered": store.conflict_candidates_considered,
        "llm_checks": store.conflict_llm_checks,
        "scope_filtered": store.conflict_scope_filtered,
        "contradictions_found": store.conflict_contradictions_found,
    }
    run_trace = {
        "query": query,
        "mode": mode,
        "llm_model": config.llm_model if config else "unknown",
        "total_steps": len(store.step_history),
        "termination_reason": store.termination_reason,
        "sub_questions_total": len(store.sub_questions),
        "sub_questions_covered": sum(1 for sq in store.sub_questions if sq.has_evidence),
        "claim_groups_total": len(store.claim_groups),
        "disputes": sum(1 for g in store.claim_groups if g.status.value == "disputed"),
        "conflict_diagnostics": conflict_diagnostics,
        "step_results": [s.result.value for s in store.step_history],
        "step_diagnostics": [
            {
                "step": s.step,
                "action": s.action,
                "result": s.result.value,
                "retrieved_results": s.retrieved_results,
                "observations_added": s.observations_added,
                "extracted_claims": s.extracted_claims,
                "result_reason": s.result_reason,
                "recovery_attempts": s.recovery_attempts,
                "recovery_strategy": s.recovery_strategy,
                "query_variants_tried": s.query_variants_tried,
                "rerank_in_count": s.rerank_in_count,
                "rerank_out_count": s.rerank_out_count,
                "claims_filtered_out": s.claims_filtered_out,
                "adjacent_claims_added": s.adjacent_claims_added,
                "direct_claims_added": s.direct_claims_added,
                "direct_claim_conversion_rate": s.direct_claim_conversion_rate,
                "query_compression_attempts": s.query_compression_attempts,
                "query_compression_llm_successes": s.query_compression_llm_successes,
                "query_compression_fallback_truncations": s.query_compression_fallback_truncations,
                "query_compression_chars_saved": s.query_compression_chars_saved,
            }
            for s in store.step_history
        ],
        "adjacent_claims_total": len(store.adjacent_claims),
        "direct_claims_total": len(store.claims),
        "overall_direct_claim_conversion_rate": round(
            len(store.claims) / max(len(store.claims) + len(store.adjacent_claims), 1), 3
        ),
        "query_compression_stats": {
            "attempts": sum(1 for e in retriever.get_query_prep_events_since(0) if e.get("compression_attempted")),
            "llm_successes": sum(1 for e in retriever.get_query_prep_events_since(0) if e.get("compression_method") == "llm"),
            "fallback_truncations": sum(1 for e in retriever.get_query_prep_events_since(0) if e.get("compression_fallback_used")),
            "avg_chars_saved": round(
                (
                    sum(int(e.get("compression_saved_chars", 0)) for e in retriever.get_query_prep_events_since(0))
                    / max(len(retriever.get_query_prep_events_since(0)), 1)
                ),
                2,
            ),
        },
        "llm_calls_total": len(store.llm_calls),
        "llm_calls_by_component": {
            "decomposer": sum(1 for c in store.llm_calls if c.component == "decomposer"),
            "extractor": sum(1 for c in store.llm_calls if c.component == "extractor"),
            "conflict": sum(1 for c in store.llm_calls if c.component == "conflict"),
            "report": sum(1 for c in store.llm_calls if c.component == "report"),
            "recovery": sum(1 for c in store.llm_calls if c.component == "recovery"),
            "query_rewriter": sum(1 for c in store.llm_calls if c.component == "query_rewriter"),
            "reranker": sum(1 for c in store.llm_calls if c.component == "reranker"),
            "claim_filter": sum(1 for c in store.llm_calls if c.component == "claim_filter"),
            "other": sum(1 for c in store.llm_calls if c.component not in {"decomposer", "extractor", "conflict", "report", "recovery", "query_rewriter", "reranker", "claim_filter"}),
        },
        "llm_calls": [c.model_dump() for c in store.llm_calls],
        "prompt_versions": session_versions(),
        **metrics,
    }
    (output_dir / "run_trace.json").write_text(json.dumps(run_trace, indent=2))
    generate_dashboard(store, run_trace, output_dir / "dashboard.html")

    print(f"[done] output → {output_dir}")
    return run_trace
