import time
from threading import Lock
from copy import copy
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any

from src.agent.config import Config, LLMProvider
from src.agent.domain_policy import DomainQualityPolicy
from src.agent.llm import LLMClient

_SEARCH_RETRIES = 3
_SEARCH_RETRY_SECS = 5
_MAX_QUERY_CHARS = 400
_GROQ_DEFAULT_QUERY_COMPRESSOR_MODEL = "llama-3.1-8b-instant"

# Non-text sources — no parseable article content for claim extraction
_EXCLUDED_DOMAINS = [
    "youtube.com", "youtu.be",
    "vimeo.com",
    "twitter.com", "x.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
    "facebook.com",
]

_NON_TEXT_DOMAINS = [
    "imgur.com",
    "i.imgur.com",
    "pinterest.com",
    "pin.it",
    "flickr.com",
    "giphy.com",
    "tenor.com",
    "gettyimages.com",
    "shutterstock.com",
    "istockphoto.com",
    "unsplash.com",
    "pexels.com",
    "twitch.tv",
    "tiktok.com",
    "dailymotion.com",
]

_NON_TEXT_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a",
)

@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    domain: str
    domain_score: float


class Retriever:
    def __init__(self, config: Config):
        self.config = config
        default_policy = DomainQualityPolicy()
        self.domain_policy = DomainQualityPolicy(
            research_domains=(
                list(config.domain_policy_research_domains)
                if config.domain_policy_research_domains is not None
                else default_policy.research_domains
            ),
            low_trust_domains=(
                list(config.domain_policy_low_trust_domains)
                if config.domain_policy_low_trust_domains is not None
                else default_policy.low_trust_domains
            ),
            high_score=(
                config.domain_policy_high_score
                if config.domain_policy_high_score is not None
                else default_policy.high_score
            ),
            medium_high_score=(
                config.domain_policy_medium_high_score
                if config.domain_policy_medium_high_score is not None
                else default_policy.medium_high_score
            ),
            medium_score=(
                config.domain_policy_medium_score
                if config.domain_policy_medium_score is not None
                else default_policy.medium_score
            ),
            low_score=(
                config.domain_policy_low_score
                if config.domain_policy_low_score is not None
                else default_policy.low_score
            ),
        )
        self._client: Any = None
        self._query_compressor: LLMClient | None = None
        self._query_prep_lock = Lock()
        self._query_prep_events: list[dict] = []
        self._search_event_lock = Lock()
        self._search_call_events: list[dict] = []
        if config.search_backend == "tavily":
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=config.tavily_api_key)
        if (
            not config.mock_mode
            and config.enable_query_compressor
            and len(config.query_compressor_model.strip()) > 0
            and config.llm_provider != LLMProvider.MOCK
        ):
            incompatible_minimax_default = (
                config.llm_provider == LLMProvider.MINIMAX
                and config.query_compressor_model.strip() == _GROQ_DEFAULT_QUERY_COMPRESSOR_MODEL
            )
            if incompatible_minimax_default:
                # Avoid invalid-model retries when using MiniMax with Groq-specific default compressor model.
                print(
                    "  [query compressor] disabled: model "
                    f"'{config.query_compressor_model}' is not valid for MiniMax"
                )
            else:
                compressor_cfg = copy(config)
                compressor_cfg.llm_model = config.query_compressor_model
                try:
                    self._query_compressor = LLMClient(compressor_cfg)
                except Exception:
                    self._query_compressor = None

    def search(self, query: str, max_results: int = 5, research_mode: bool = False) -> list[SearchResult]:
        if self.config.search_backend == "mock":
            return self._mock_search(query)
        safe_query, prep_meta = self._prepare_query(query)
        with self._query_prep_lock:
            self._query_prep_events.append(dict(prep_meta))
        start = time.perf_counter()
        retries = 0
        for attempt in range(_SEARCH_RETRIES):
            try:
                search_kwargs = dict(
                    max_results=max_results,
                    include_raw_content=True,
                )
                if research_mode:
                    search_kwargs["include_domains"] = self.domain_policy.research_domains
                else:
                    search_kwargs["exclude_domains"] = _EXCLUDED_DOMAINS
                results = self._client.search(safe_query, **search_kwargs)
                filtered = [
                    SearchResult(
                        url=r["url"],
                        title=r.get("title", ""),
                        snippet=(r.get("raw_content") or r.get("content", ""))[:800],
                        domain=self._extract_domain(r["url"]),
                        domain_score=self._domain_quality_score(self._extract_domain(r["url"])),
                    )
                    for r in results.get("results", [])
                    if self._is_text_result(
                        url=r.get("url", ""),
                        title=r.get("title", ""),
                        snippet=(r.get("raw_content") or r.get("content", "")),
                    )
                ]
                self._record_search_event(
                    retries=retries,
                    success=True,
                    elapsed_ms=int((time.perf_counter() - start) * 1000),
                )
                return filtered[:max_results]
            except Exception as e:
                if attempt < _SEARCH_RETRIES - 1:
                    retries += 1
                    print(f"  [search retry {attempt + 1}/{_SEARCH_RETRIES}] {e}")
                    time.sleep(_SEARCH_RETRY_SECS)
                else:
                    self._record_search_event(
                        retries=retries,
                        success=False,
                        elapsed_ms=int((time.perf_counter() - start) * 1000),
                    )
                    raise
        return []

    def _extract_domain(self, url: str) -> str:
        return urlparse(url).netloc

    def _domain_quality_score(self, domain: str) -> float:
        return self.domain_policy.score(domain)

    def _prepare_query(self, query: str) -> tuple[str, dict]:
        compact = " ".join((query or "").split())
        original_len = len(compact)
        if len(compact) <= _MAX_QUERY_CHARS:
            prep_meta = {
                "compression_attempted": False,
                "compression_method": "none",
                "compression_model": "",
                "original_query_len": original_len,
                "compressed_query_len": original_len,
                "compression_saved_chars": 0,
                "compression_fallback_used": False,
            }
            return compact, prep_meta
        compressed = self._compress_query(compact)
        if compressed:
            compressed = " ".join(compressed.split())
            if len(compressed) <= _MAX_QUERY_CHARS:
                prep_meta = {
                    "compression_attempted": True,
                    "compression_method": "llm",
                    "compression_model": self.config.query_compressor_model,
                    "original_query_len": original_len,
                    "compressed_query_len": len(compressed),
                    "compression_saved_chars": max(0, original_len - len(compressed)),
                    "compression_fallback_used": False,
                }
                return compressed, prep_meta
            truncated = compressed[:_MAX_QUERY_CHARS].rsplit(" ", 1)[0].strip()
            prep_meta = {
                "compression_attempted": True,
                "compression_method": "truncate",
                "compression_model": self.config.query_compressor_model,
                "original_query_len": original_len,
                "compressed_query_len": len(truncated),
                "compression_saved_chars": max(0, original_len - len(truncated)),
                "compression_fallback_used": True,
            }
            return truncated, prep_meta
        # Keep as much semantic context as possible within Tavily's query limit.
        truncated = compact[:_MAX_QUERY_CHARS].rsplit(" ", 1)[0].strip()
        prep_meta = {
            "compression_attempted": True,
            "compression_method": "truncate",
            "compression_model": "",
            "original_query_len": original_len,
            "compressed_query_len": len(truncated),
            "compression_saved_chars": max(0, original_len - len(truncated)),
            "compression_fallback_used": True,
        }
        return truncated, prep_meta

    def _compress_query(self, query: str) -> str:
        if self._query_compressor is None:
            return ""
        system = (
            "Compress search queries while preserving intent and key entities.\n"
            f"Return plain text only, max {_MAX_QUERY_CHARS} characters.\n"
            "Keep research-specific terms like benchmark names, constraints, and failure modes."
        )
        user = f"Original query:\n{query}\n\nCompressed query:"
        try:
            return self._query_compressor.complete(system, user).strip().splitlines()[0].strip()
        except Exception:
            return ""

    def get_query_prep_event_count(self) -> int:
        with self._query_prep_lock:
            return len(self._query_prep_events)

    def get_query_prep_events_since(self, start_idx: int) -> list[dict]:
        if start_idx < 0:
            start_idx = 0
        with self._query_prep_lock:
            return [dict(e) for e in self._query_prep_events[start_idx:]]

    def suggest_parallelism(self, requested_parallelism: int, window: int = 20) -> int:
        if requested_parallelism <= 1:
            return 1
        with self._search_event_lock:
            recent = self._search_call_events[-window:]
        if not recent:
            return requested_parallelism
        retry_ratio = sum(1 for e in recent if int(e.get("retries", 0)) > 0) / len(recent)
        failure_ratio = sum(1 for e in recent if not bool(e.get("success", True))) / len(recent)
        if failure_ratio >= 0.20 or retry_ratio >= 0.50:
            return 1
        if retry_ratio >= 0.25:
            return max(1, requested_parallelism // 2)
        return requested_parallelism

    def _record_search_event(self, retries: int, success: bool, elapsed_ms: int) -> None:
        with self._search_event_lock:
            self._search_call_events.append(
                {
                    "retries": retries,
                    "success": success,
                    "elapsed_ms": elapsed_ms,
                }
            )

    def _is_text_result(self, url: str, title: str, snippet: str) -> bool:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        blocked_domains = set(_EXCLUDED_DOMAINS) | set(_NON_TEXT_DOMAINS)
        if any(domain == d or domain.endswith(f".{d}") for d in blocked_domains):
            return False

        if path.endswith(_NON_TEXT_EXTENSIONS):
            return False

        non_text_markers = (
            "/video/", "/videos/", "/watch", "/shorts/", "/reel/", "/reels/",
            "/image/", "/images/", "/photo/", "/photos/", "/gallery/",
        )
        if any(marker in path for marker in non_text_markers):
            return False

        title_l = title.lower()
        snippet_l = snippet.lower()
        bad_title_markers = ("youtube", "vimeo", "tiktok", "watch now", "photo gallery")
        if any(marker in title_l for marker in bad_title_markers):
            return False

        # Tavily sometimes returns thin or non-article results with almost no textual body.
        if len((snippet or "").strip()) < 80:
            return False

        if any(ext in snippet_l for ext in (".jpg", ".png", ".gif", ".mp4", ".webm")):
            return False

        return True

    def _mock_search(self, query: str) -> list[SearchResult]:
        short = query[:40]
        return [
            SearchResult(
                url=f"https://source-{i}.example.com/research",
                title=f"Research on {short} — Source {i}",
                snippet=(
                    f"Empirical study {i}: Research on '{short}' shows measurable effects "
                    f"in controlled conditions. Source {i} provides independent replication "
                    f"with sample size n=200. Limitations include short follow-up period."
                    if i % 2 == 1 else
                    f"Critical review {i}: While initial findings on '{short}' appear promising, "
                    f"several methodological concerns limit generalizability. Effect sizes vary "
                    f"considerably across populations and settings."
                ),
                domain=f"source-{i}.example.com",
                domain_score=self.domain_policy.medium_score,
            )
            for i in range(1, 4)
        ]
