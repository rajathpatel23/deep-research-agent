from dataclasses import dataclass, field


@dataclass
class DomainQualityPolicy:
    """Simple, explicit scoring policy for source quality."""

    research_domains: list[str] = field(default_factory=lambda: [
        "arxiv.org",
        "semanticscholar.org",
        "aclanthology.org",
        "openreview.net",
        "proceedings.mlr.press",
        "jmlr.org",
        "neurips.cc",
        "research.google",
        "anthropic.com",
        "openai.com",
        "deepmind.google",
        "deepmind.com",
        "ai.meta.com",
        "huggingface.co",
        "mistral.ai",
    ])
    low_trust_domains: list[str] = field(default_factory=lambda: [
        "researchgate.net",
        "emergentmind.com",
        "aipromptsdirectory.com",
        "analytics.usa.gov",
        "linkedin.com",
    ])
    high_score: float = 0.9
    medium_high_score: float = 0.75
    medium_score: float = 0.5
    low_score: float = 0.2

    def score(self, domain: str) -> float:
        d = (domain or "").lower()
        if self._matches_any(d, self.research_domains):
            return self.high_score
        if self._matches_any(d, self.low_trust_domains):
            return self.low_score
        if d.endswith(".edu") or d.endswith(".gov"):
            return self.medium_high_score
        return self.medium_score

    @staticmethod
    def _matches_any(domain: str, candidates: list[str]) -> bool:
        return any(domain == cd or domain.endswith(f".{cd}") for cd in candidates)
