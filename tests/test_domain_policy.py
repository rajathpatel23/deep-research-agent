from src.agent.domain_policy import DomainQualityPolicy


def test_research_domain_scores_high():
    policy = DomainQualityPolicy()
    assert policy.score("arxiv.org") == 0.9
    assert policy.score("www.semanticscholar.org") == 0.9


def test_low_trust_domain_scores_low():
    policy = DomainQualityPolicy()
    assert policy.score("www.researchgate.net") == 0.2
    assert policy.score("www.linkedin.com") == 0.2


def test_edu_domain_scores_medium_high():
    policy = DomainQualityPolicy()
    assert policy.score("cs.stanford.edu") == 0.75


def test_unknown_domain_scores_medium():
    policy = DomainQualityPolicy()
    assert policy.score("example.com") == 0.5
