from src.agent.config import Config, LLMProvider, SearchBackend
from src.agent.retriever import Retriever


def _config() -> Config:
    return Config(
        llm_provider=LLMProvider.MOCK,
        llm_model="mock",
        search_backend=SearchBackend.MOCK,
        groq_api_key=None,
        anthropic_api_key=None,
        nebius_api_key=None,
        tavily_api_key=None,
        mock_mode=True,
    )


def test_text_result_is_allowed():
    retriever = Retriever(_config())
    assert retriever._is_text_result(
        url="https://example.com/research/article",
        title="A research article on chain-of-thought",
        snippet="This article reports empirical findings on chain-of-thought generalization under distribution shift." * 2,
    ) is True


def test_video_domain_is_blocked():
    retriever = Retriever(_config())
    assert retriever._is_text_result(
        url="https://youtube.com/watch?v=abc123",
        title="Watch now: chain-of-thought explained",
        snippet="Long enough snippet but from a video domain." * 5,
    ) is False


def test_image_extension_is_blocked():
    retriever = Retriever(_config())
    assert retriever._is_text_result(
        url="https://example.com/images/figure.png",
        title="Figure 1",
        snippet="Long enough snippet but points to an image asset." * 5,
    ) is False


def test_gallery_path_is_blocked():
    retriever = Retriever(_config())
    assert retriever._is_text_result(
        url="https://example.com/gallery/research-photos",
        title="Research photo gallery",
        snippet="Long enough snippet but this is a gallery page." * 5,
    ) is False


def test_thin_snippet_is_blocked():
    retriever = Retriever(_config())
    assert retriever._is_text_result(
        url="https://example.com/article",
        title="Article",
        snippet="Too short",
    ) is False


def test_prepare_query_normalizes_whitespace():
    retriever = Retriever(_config())
    query = "  chain-of-thought   reasoning \n\n benchmarks  "
    assert retriever._prepare_query(query) == "chain-of-thought reasoning benchmarks"


def test_prepare_query_truncates_to_tavily_limit():
    retriever = Retriever(_config())
    long_query = "token " * 120  # > 400 chars
    prepared = retriever._prepare_query(long_query)
    assert len(prepared) <= 400
    assert prepared.endswith("token")


def test_prepare_query_prefers_compressed_query_when_available():
    retriever = Retriever(_config())

    class _Compressor:
        def complete(self, system: str, user: str, trace=None, model_override=None) -> str:
            return "compressed query about cot benchmarks failures and limitations"

    retriever._query_compressor = _Compressor()
    long_query = "token " * 120
    prepared = retriever._prepare_query(long_query)
    assert prepared == "compressed query about cot benchmarks failures and limitations"


def test_prepare_query_sets_compression_metadata():
    retriever = Retriever(_config())
    long_query = "token " * 120
    _ = retriever._prepare_query(long_query)
    meta = retriever._last_query_prep_meta
    assert meta["compression_attempted"] is True
    assert meta["compressed_query_len"] <= 400
    assert meta["compression_saved_chars"] > 0


def test_domain_quality_score_high_for_research_domains():
    retriever = Retriever(_config())
    assert retriever._domain_quality_score("arxiv.org") == 0.9
    assert retriever._domain_quality_score("www.semanticscholar.org") == 0.9


def test_domain_quality_score_low_for_known_noisy_domains():
    retriever = Retriever(_config())
    assert retriever._domain_quality_score("www.researchgate.net") == 0.2
    assert retriever._domain_quality_score("www.linkedin.com") == 0.2


def test_domain_quality_score_defaults_to_medium():
    retriever = Retriever(_config())
    assert retriever._domain_quality_score("example.com") == 0.5


def test_domain_quality_policy_can_be_overridden_from_config():
    cfg = _config()
    cfg.domain_policy_research_domains = ["trusted.example"]
    cfg.domain_policy_low_trust_domains = ["noisy.example"]
    cfg.domain_policy_high_score = 0.95
    cfg.domain_policy_medium_high_score = 0.7
    cfg.domain_policy_medium_score = 0.45
    cfg.domain_policy_low_score = 0.1
    retriever = Retriever(cfg)
    assert retriever._domain_quality_score("paper.trusted.example") == 0.95
    assert retriever._domain_quality_score("forum.noisy.example") == 0.1
    assert retriever._domain_quality_score("college.edu") == 0.7
    assert retriever._domain_quality_score("unknown.example") == 0.45
