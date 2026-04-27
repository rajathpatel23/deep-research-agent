from src.agent.prompt_registry import get_prompt, reset_session, session_versions


def setup_function():
    reset_session()


def test_get_prompt_returns_dict_with_system():
    prompt = get_prompt("decomposer")
    assert "system" in prompt
    assert isinstance(prompt["system"], str)
    assert len(prompt["system"]) > 0


def test_get_prompt_has_version():
    prompt = get_prompt("decomposer")
    assert "version" in prompt


def test_all_modules_loadable():
    for module in ("decomposer", "extractor", "conflict", "report"):
        prompt = get_prompt(module)
        assert "system" in prompt


def test_session_versions_recorded():
    reset_session()
    get_prompt("decomposer")
    get_prompt("extractor")
    versions = session_versions()
    assert "decomposer" in versions
    assert "extractor" in versions


def test_reset_clears_session():
    get_prompt("decomposer")
    reset_session()
    assert session_versions() == {}
