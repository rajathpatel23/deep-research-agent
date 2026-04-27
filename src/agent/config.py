import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class LLMProvider(str, Enum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    NEBIUS = "nebius"
    MINIMAX = "minimax"
    OLLAMA = "ollama"
    MOCK = "mock"


class SearchBackend(str, Enum):
    TAVILY = "tavily"
    MOCK = "mock"


class GroqModel(str, Enum):
    QWEN3_32B = "qwen/qwen3-32b"
    LLAMA_3_1_70B = "llama-3.1-70b-versatile"
    LLAMA_3_3_70B = "llama-3.3-70b-versatile"


class AnthropicModel(str, Enum):
    HAIKU_4_5 = "claude-haiku-4-5-20251001"
    SONNET_4_6 = "claude-sonnet-4-6"


class OllamaModel(str, Enum):
    QWEN3_14B = "qwen3:14b"
    QWEN3_8B = "qwen3:8b"
    QWEN3_32B = "qwen3:32b"


@dataclass
class Config:
    llm_provider: LLMProvider
    llm_model: str
    search_backend: SearchBackend
    groq_api_key: Optional[str]
    anthropic_api_key: Optional[str]
    nebius_api_key: Optional[str]
    minimax_api_key: Optional[str]
    tavily_api_key: Optional[str]
    max_steps: int = 10
    max_results: int = 3
    research_mode: bool = True
    enable_recovery: bool = True
    recovery_max_attempts: int = 2
    query_rewrite_variants: int = 3
    rerank_top_k: int = 4
    search_parallelism: int = 1
    adaptive_parallelism: bool = True
    extract_parallelism: int = 1
    enable_claim_filter: bool = True
    diminishing_window: int = 4
    min_coverage_for_diminishing: float = 0.4
    enable_query_compressor: bool = True
    query_compressor_model: str = "llama-3.1-8b-instant"
    min_direct_domain_score: float = 0.3
    domain_policy_research_domains: Optional[list[str]] = None
    domain_policy_low_trust_domains: Optional[list[str]] = None
    domain_policy_high_score: Optional[float] = None
    domain_policy_medium_high_score: Optional[float] = None
    domain_policy_medium_score: Optional[float] = None
    domain_policy_low_score: Optional[float] = None
    mock_mode: bool = False


def load_config() -> Config:
    mock_mode = os.getenv("MOCK", "false").lower() == "true"
    llm_provider = LLMProvider.MOCK if mock_mode else LLMProvider(os.getenv("LLM_PROVIDER", "groq"))
    search_backend = SearchBackend.MOCK if mock_mode else SearchBackend(os.getenv("SEARCH_BACKEND", "tavily"))
    return Config(
        llm_provider=llm_provider,
        llm_model=os.getenv("LLM_MODEL", GroqModel.QWEN3_32B.value),
        search_backend=search_backend,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        nebius_api_key=os.getenv("NEBIUS_API_KEY"),
        minimax_api_key=os.getenv("MINIMAX_API_KEY"),
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        research_mode=os.getenv("RESEARCH_MODE", "true").lower() == "true",
        enable_recovery=os.getenv("ENABLE_RECOVERY", "true").lower() == "true",
        recovery_max_attempts=int(os.getenv("RECOVERY_MAX_ATTEMPTS", "2")),
        query_rewrite_variants=int(os.getenv("QUERY_REWRITE_VARIANTS", "3")),
        rerank_top_k=int(os.getenv("RERANK_TOP_K", "4")),
        search_parallelism=max(1, int(os.getenv("SEARCH_PARALLELISM", "1"))),
        adaptive_parallelism=os.getenv("ADAPTIVE_PARALLELISM", "true").lower() == "true",
        extract_parallelism=max(1, int(os.getenv("EXTRACT_PARALLELISM", "1"))),
        enable_claim_filter=os.getenv("ENABLE_CLAIM_FILTER", "true").lower() == "true",
        diminishing_window=int(os.getenv("DIMINISHING_WINDOW", "4")),
        min_coverage_for_diminishing=float(os.getenv("MIN_COVERAGE_FOR_DIMINISHING", "0.4")),
        enable_query_compressor=os.getenv("ENABLE_QUERY_COMPRESSOR", "true").lower() == "true",
        query_compressor_model=os.getenv("QUERY_COMPRESSOR_MODEL", "llama-3.1-8b-instant"),
        min_direct_domain_score=float(os.getenv("MIN_DIRECT_DOMAIN_SCORE", "0.3")),
        mock_mode=mock_mode,
    )
