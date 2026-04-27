import warnings

import pytest

from src.agent.config import Config, LLMProvider, SearchBackend
from src.agent.search_clients import (
    MiniMaxSearchClient,
    MockSearchClient,
    RawSearchResult,
    TavilySearchClient,
    build_search_client,
)


def _config(backend: SearchBackend, **overrides) -> Config:
    base = dict(
        llm_provider=LLMProvider.MOCK,
        llm_model="mock",
        search_backend=backend,
        groq_api_key=None,
        anthropic_api_key=None,
        nebius_api_key=None,
        minimax_api_key=None,
        tavily_api_key=None,
        mock_mode=True,
    )
    base.update(overrides)
    return Config(**base)


def test_raw_search_result_defaults_raw_content_to_empty():
    r = RawSearchResult(url="https://x.test", title="t", snippet="s")
    assert r.raw_content == ""


def test_mock_client_returns_three_fixture_results():
    client = MockSearchClient()
    results = client.search("anything", max_results=10)
    assert len(results) == 3
    assert all(isinstance(r, RawSearchResult) for r in results)
    assert results[0].url == "https://source-1.example.com/research"


def test_mock_client_caps_at_max_results():
    client = MockSearchClient()
    results = client.search("anything", max_results=2)
    assert len(results) == 2


def test_minimax_client_requires_api_key():
    with pytest.raises(ValueError, match="MINIMAX_API_KEY"):
        MiniMaxSearchClient(api_key=None)
    with pytest.raises(ValueError, match="MINIMAX_API_KEY"):
        MiniMaxSearchClient(api_key="")


def test_tavily_client_requires_api_key():
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        TavilySearchClient(api_key=None)


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


def _install_fake_post(client: MiniMaxSearchClient, response_payload: dict):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(response_payload)

    client._session.post = fake_post  # type: ignore[assignment]
    return captured


def _make_minimax_client() -> MiniMaxSearchClient:
    # Reset the one-time warning so tests don't depend on order.
    MiniMaxSearchClient._RAW_CONTENT_WARNING_EMITTED = False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return MiniMaxSearchClient(api_key="fake-key", api_host="https://api.example")


def test_minimax_client_posts_to_coding_plan_search_endpoint():
    client = _make_minimax_client()
    captured = _install_fake_post(
        client,
        {"organic": [], "base_resp": {"status_code": 0, "status_msg": "ok"}},
    )
    client.search("hello world", max_results=5)
    assert captured["url"] == "https://api.example/v1/coding_plan/search"
    assert captured["json"] == {"q": "hello world"}
    assert captured["timeout"] == 30


def test_minimax_client_normalizes_organic_results():
    client = _make_minimax_client()
    _install_fake_post(
        client,
        {
            "organic": [
                {"title": "First", "link": "https://a.test/x", "snippet": "snippet a"},
                {"title": "Second", "link": "https://b.test/y", "snippet": "snippet b"},
            ],
            "base_resp": {"status_code": 0},
        },
    )
    results = client.search("q", max_results=5)
    assert len(results) == 2
    assert results[0] == RawSearchResult(
        url="https://a.test/x", title="First", snippet="snippet a", raw_content=""
    )
    assert all(r.raw_content == "" for r in results)


def test_minimax_client_truncates_to_max_results():
    client = _make_minimax_client()
    _install_fake_post(
        client,
        {
            "organic": [
                {"title": f"r{i}", "link": f"https://x.test/{i}", "snippet": f"s{i}"}
                for i in range(10)
            ],
            "base_resp": {"status_code": 0},
        },
    )
    results = client.search("q", max_results=3)
    assert len(results) == 3
    assert [r.url for r in results] == [
        "https://x.test/0",
        "https://x.test/1",
        "https://x.test/2",
    ]


def test_minimax_client_skips_results_without_link():
    client = _make_minimax_client()
    _install_fake_post(
        client,
        {
            "organic": [
                {"title": "no link"},
                {"title": "good", "link": "https://ok.test", "snippet": "s"},
                {"title": "empty link", "link": ""},
            ],
            "base_resp": {"status_code": 0},
        },
    )
    results = client.search("q", max_results=5)
    assert len(results) == 1
    assert results[0].url == "https://ok.test"


def test_minimax_client_raises_on_nonzero_base_resp():
    client = _make_minimax_client()
    _install_fake_post(
        client,
        {
            "organic": [],
            "base_resp": {"status_code": 1004, "status_msg": "auth failed"},
        },
    )
    with pytest.raises(RuntimeError, match="1004"):
        client.search("q", max_results=5)


def test_minimax_client_caps_snippet_at_800_chars():
    client = _make_minimax_client()
    long_snippet = "x" * 2000
    _install_fake_post(
        client,
        {
            "organic": [{"title": "t", "link": "https://x.test", "snippet": long_snippet}],
            "base_resp": {"status_code": 0},
        },
    )
    results = client.search("q", max_results=1)
    assert len(results[0].snippet) == 800


def test_minimax_client_sets_authorization_header():
    MiniMaxSearchClient._RAW_CONTENT_WARNING_EMITTED = False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        client = MiniMaxSearchClient(api_key="abc123", api_host="https://api.example")
    assert client._session.headers["Authorization"] == "Bearer abc123"


def test_minimax_client_emits_raw_content_warning_once():
    MiniMaxSearchClient._RAW_CONTENT_WARNING_EMITTED = False
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        MiniMaxSearchClient(api_key="k1")
        MiniMaxSearchClient(api_key="k2")
    user_warnings = [x for x in w if issubclass(x.category, UserWarning)]
    assert len(user_warnings) == 1
    assert "snippets only" in str(user_warnings[0].message)


def test_build_search_client_dispatches_mock():
    cfg = _config(SearchBackend.MOCK)
    client = build_search_client(cfg)
    assert isinstance(client, MockSearchClient)


def test_build_search_client_dispatches_minimax():
    MiniMaxSearchClient._RAW_CONTENT_WARNING_EMITTED = False
    cfg = _config(SearchBackend.MINIMAX, minimax_api_key="fake")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        client = build_search_client(cfg)
    assert isinstance(client, MiniMaxSearchClient)


def test_build_search_client_dispatches_tavily():
    cfg = _config(SearchBackend.TAVILY, tavily_api_key="fake")
    client = build_search_client(cfg)
    assert isinstance(client, TavilySearchClient)


def test_build_search_client_propagates_missing_minimax_key():
    cfg = _config(SearchBackend.MINIMAX, minimax_api_key=None)
    with pytest.raises(ValueError, match="MINIMAX_API_KEY"):
        build_search_client(cfg)


def test_build_search_client_propagates_missing_tavily_key():
    cfg = _config(SearchBackend.TAVILY, tavily_api_key=None)
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        build_search_client(cfg)
