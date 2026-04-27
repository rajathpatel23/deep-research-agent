"""Search backend clients (Strategy pattern).

`Retriever` owns cross-cutting concerns (query prep, retries, filtering, domain
scoring). Each `SearchClient` is responsible only for talking to one specific
search API and returning normalized `RawSearchResult`s. Add a new backend by
implementing the `SearchClient` protocol and registering it in
`build_search_client`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Optional, Protocol

import requests

from src.agent.config import Config, SearchBackend


@dataclass
class RawSearchResult:
    """Normalized search result before Retriever post-processing.

    `raw_content` is the full page text when the backend supplies it
    (Tavily does; MiniMax coding-plan search does not). Empty string means
    "snippet is the only text we have" — downstream claim extraction will
    operate on the snippet only.
    """
    url: str
    title: str
    snippet: str
    raw_content: str = ""


class SearchClient(Protocol):
    def search(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> list[RawSearchResult]: ...


class TavilySearchClient:
    def __init__(self, api_key: Optional[str]):
        if not api_key:
            raise ValueError("TAVILY_API_KEY is required for tavily search backend")
        from tavily import TavilyClient
        self._client = TavilyClient(api_key=api_key)

    def search(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> list[RawSearchResult]:
        kwargs: dict[str, Any] = {
            "max_results": max_results,
            "include_raw_content": True,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains
        if exclude_domains:
            kwargs["exclude_domains"] = exclude_domains
        response = self._client.search(query, **kwargs)
        out: list[RawSearchResult] = []
        for r in response.get("results", []):
            url = r.get("url", "")
            if not url:
                continue
            out.append(
                RawSearchResult(
                    url=url,
                    title=r.get("title", "") or "",
                    snippet=(r.get("raw_content") or r.get("content", "") or "")[:800],
                    raw_content=r.get("raw_content") or "",
                )
            )
        return out


class MiniMaxSearchClient:
    """MiniMax coding-plan web search.

    API: POST {host}/v1/coding_plan/search with body {"q": query}. Endpoint
    only accepts a query string; `max_results`, `include_domains`,
    `exclude_domains` are NOT supported natively. Domain filtering is handled
    post-search by `Retriever._is_text_result` and the domain scoring policy.

    Note: response only contains snippets, not raw page content. This is a
    quality downgrade vs Tavily for downstream claim extraction.
    """

    _RAW_CONTENT_WARNING_EMITTED = False

    def __init__(self, api_key: Optional[str], api_host: str = "https://api.minimax.io"):
        if not api_key:
            raise ValueError("MINIMAX_API_KEY is required for minimax search backend")
        self._api_host = api_host.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "MM-API-Source": "deep-research-agent",
            "Content-Type": "application/json",
        })
        if not MiniMaxSearchClient._RAW_CONTENT_WARNING_EMITTED:
            warnings.warn(
                "MiniMax coding-plan search returns snippets only (no raw page "
                "content). Downstream claim extraction will operate on shorter "
                "text than with Tavily. Use SEARCH_BACKEND=tavily if full-text "
                "extraction matters for your experiment.",
                stacklevel=2,
            )
            MiniMaxSearchClient._RAW_CONTENT_WARNING_EMITTED = True

    def search(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> list[RawSearchResult]:
        url = f"{self._api_host}/v1/coding_plan/search"
        response = self._session.post(url, json={"q": query}, timeout=30)
        response.raise_for_status()
        data = response.json()

        base_resp = data.get("base_resp") or {}
        if base_resp.get("status_code", 0) != 0:
            raise RuntimeError(
                f"MiniMax search error {base_resp.get('status_code')}: "
                f"{base_resp.get('status_msg', 'unknown')}"
            )

        organic = data.get("organic") or []
        out: list[RawSearchResult] = []
        for r in organic[:max_results]:
            link = r.get("link") or r.get("url") or ""
            if not link:
                continue
            snippet = (r.get("snippet") or "").strip()
            out.append(
                RawSearchResult(
                    url=link,
                    title=(r.get("title") or "").strip(),
                    snippet=snippet[:800],
                    raw_content="",
                )
            )
        return out


class MockSearchClient:
    """Deterministic fixture results for offline tests / mock_mode runs."""

    def search(
        self,
        query: str,
        max_results: int,
        include_domains: Optional[list[str]] = None,
        exclude_domains: Optional[list[str]] = None,
    ) -> list[RawSearchResult]:
        short = (query or "")[:40]
        results = [
            RawSearchResult(
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
                raw_content="",
            )
            for i in range(1, 4)
        ]
        return results[:max_results]


def build_search_client(config: Config) -> SearchClient:
    backend = config.search_backend
    if backend == SearchBackend.TAVILY:
        return TavilySearchClient(api_key=config.tavily_api_key)
    if backend == SearchBackend.MINIMAX:
        return MiniMaxSearchClient(
            api_key=config.minimax_api_key,
            api_host=config.minimax_api_host,
        )
    if backend == SearchBackend.MOCK:
        return MockSearchClient()
    raise ValueError(f"Unsupported search backend: {backend!r}")
