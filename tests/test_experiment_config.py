from src.agent.experiment_config import load_experiment


def test_experiment_domain_policy_maps_to_agent_config():
    exp = load_experiment("experiments/ablation_llama8b_phase1.yaml")
    cfg = exp.to_agent_config()
    assert cfg.domain_policy_research_domains is not None
    assert "arxiv.org" in cfg.domain_policy_research_domains
    assert cfg.domain_policy_low_trust_domains is not None
    assert "researchgate.net" in cfg.domain_policy_low_trust_domains
    assert cfg.domain_policy_high_score == 0.9
    assert cfg.domain_policy_medium_high_score == 0.75
    assert cfg.domain_policy_medium_score == 0.5
    assert cfg.domain_policy_low_score == 0.2
