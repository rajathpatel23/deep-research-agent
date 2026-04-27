from typing import List, Optional

import yaml
from pydantic import BaseModel, Field

from src.agent.config import Config, GroqModel, LLMProvider, SearchBackend


class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.GROQ
    model: str = GroqModel.QWEN3_32B.value


class SearchConfig(BaseModel):
    backend: SearchBackend = SearchBackend.TAVILY
    max_results: int = 5
    research_mode: bool = True


class AgentConfig(BaseModel):
    recovery_max_attempts: int = 2
    query_rewrite_variants: int = 3
    rerank_top_k: int = 4
    query_compressor_model: str = "llama-3.1-8b-instant"
    search_parallelism: int = 1
    adaptive_parallelism: bool = True
    extract_parallelism: int = 1
    enable_claim_filter: bool = True
    diminishing_window: int = 4
    min_coverage_for_diminishing: float = 0.4


class DomainPolicyConfig(BaseModel):
    research_domains: Optional[List[str]] = None
    low_trust_domains: Optional[List[str]] = None
    high_score: Optional[float] = None
    medium_high_score: Optional[float] = None
    medium_score: Optional[float] = None
    low_score: Optional[float] = None


class RunSpec(BaseModel):
    query: str
    modes: List[str] = Field(default_factory=lambda: ["guided"])
    max_steps: int = 10
    shared_sources: bool = False


class ExperimentConfig(BaseModel):
    name: str
    description: Optional[str] = None
    llm: LLMConfig = Field(default_factory=LLMConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    domain_policy: DomainPolicyConfig = Field(default_factory=DomainPolicyConfig)
    runs: List[RunSpec]
    output_dir: str = "runs"

    def to_agent_config(self, groq_api_key=None, anthropic_api_key=None,
                        nebius_api_key=None, minimax_api_key=None, tavily_api_key=None) -> Config:
        import os
        return Config(
            llm_provider=self.llm.provider,
            llm_model=self.llm.model,
            search_backend=self.search.backend,
            max_results=self.search.max_results,
            research_mode=self.search.research_mode,
            recovery_max_attempts=self.agent.recovery_max_attempts,
            query_rewrite_variants=self.agent.query_rewrite_variants,
            rerank_top_k=self.agent.rerank_top_k,
            query_compressor_model=self.agent.query_compressor_model,
            search_parallelism=max(1, self.agent.search_parallelism),
            adaptive_parallelism=self.agent.adaptive_parallelism,
            extract_parallelism=max(1, self.agent.extract_parallelism),
            enable_claim_filter=self.agent.enable_claim_filter,
            diminishing_window=self.agent.diminishing_window,
            min_coverage_for_diminishing=self.agent.min_coverage_for_diminishing,
            domain_policy_research_domains=self.domain_policy.research_domains,
            domain_policy_low_trust_domains=self.domain_policy.low_trust_domains,
            domain_policy_high_score=self.domain_policy.high_score,
            domain_policy_medium_high_score=self.domain_policy.medium_high_score,
            domain_policy_medium_score=self.domain_policy.medium_score,
            domain_policy_low_score=self.domain_policy.low_score,
            groq_api_key=groq_api_key or os.getenv("GROQ_API_KEY"),
            anthropic_api_key=anthropic_api_key or os.getenv("ANTHROPIC_API_KEY"),
            nebius_api_key=nebius_api_key or os.getenv("NEBIUS_API_KEY"),
            minimax_api_key=minimax_api_key or os.getenv("MINIMAX_API_KEY"),
            tavily_api_key=tavily_api_key or os.getenv("TAVILY_API_KEY"),
        )


def load_experiment(path: str) -> ExperimentConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return ExperimentConfig(**data)
