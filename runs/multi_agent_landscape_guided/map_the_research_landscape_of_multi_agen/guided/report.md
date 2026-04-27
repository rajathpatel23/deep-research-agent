# Research Report

**Query:** Map the research landscape of multi-agent LLM systems. Produce a structured report that includes a visual taxonomy or design graph showing the major architectural patterns, how they relate, and where the open problems are.

## Summary

Research on multi-agent LLM systems has identified several architectural patterns (hierarchical, peer-to-peer, shared-memory) with evidence suggesting coordination mechanisms like voting and consensus protocols can improve performance on specific task types, though gains vary considerably by task domain. However, multi-agent systems do not universally outperform single-agent baselines, and researchers have catalogued at least 14 distinct failure modes across three categories, including issues with error propagation and scalability. Key open problems include developing standardized evaluation benchmarks given current limitations in task coverage, metric consistency, and reproducibility.

## Findings

### What are the dominant architectural patterns in multi-agent LLM systems including hierarchical, peer-to-peer, and shared-memory designs?

**Claim:** The paper presents a systematic benchmark comparing four multi-agent orchestration architectures. [3]

- Confidence: low | Status: weak

- Scope: benchmarking multi-agent orchestration architectures


**Claim:** L2M2 is a hierarchical framework in which LLMs generate high-level strategies while MARL agents execute low-level control. [17]

- Confidence: low | Status: weak

- Scope: in the L2M2 framework architecture


**Claim:** This paper proposes a hierarchical multi-agent framework [7]

- Confidence: low | Status: weak

- Scope: general framework description


**Claim:** The framework trains a single leader LLM to coordinate several untrained companion agents [7]

- Confidence: low | Status: weak

- Scope: framework architecture and training approach


### What coordination mechanisms do multi-agent LLM systems use for agent communication and how do debate, negotiation, and consensus protocols affect system performance?

**Claim:** Voting protocols improve performance by 13.2% in reasoning tasks [8]

- Confidence: low | Status: weak

- Scope: in reasoning tasks


**Claim:** Consensus protocols improve performance by 2.8% in knowledge tasks [8]

- Confidence: low | Status: weak

- Scope: in knowledge tasks


### What empirical evidence exists for multi-agent LLM systems outperforming single-agent baselines on complex reasoning and collaborative tasks?

**Claim:** SAS consistently match or outperform MAS on multi-hop reasoning tasks when reasoning tokens are held constant. [3]

- Confidence: low | Status: weak

- Scope: when reasoning tokens are held constant


**Claim:** Multi-agent frameworks do not universally outperform single LLMs. [7]

- Confidence: low | Status: weak

- Scope: Based on the results highlighted in the study


### What are the common failure modes and limitations of multi-agent LLM systems including error propagation, scalability bottlenecks, and reward hacking? [adversarial]

**Claim:** We identified 14 distinct failure modes. [3]

- Confidence: low | Status: weak

- Scope: In our comprehensive analysis


**Claim:** The 14 distinct failure modes are clustered into 3 categories. [3]

- Confidence: low | Status: weak

- Scope: In our comprehensive analysis of failure modes


**Claim:** Current MAS frameworks have high failure rates when performing MAD analysis [7]

- Confidence: low | Status: weak

- Scope: for MAD analysis in current MAS frameworks


### What open research problems remain unsolved in multi-agent LLM systems such as agent role specialization, dynamic team formation, and evaluation benchmarks? [adversarial]

**Claim:** Existing evaluations face limited task coverage [14]

- Confidence: low | Status: weak

- Scope: general


**Claim:** Existing evaluations use inconsistent metrics [14]

- Confidence: low | Status: weak

- Scope: general


**Claim:** Existing evaluations have poor reproducibility [14]

- Confidence: low | Status: weak

- Scope: general


## Sources

[1] medium.com — https://medium.com/@princekrampah/multi-agent-architecture-in-multi-agent-systems-multi-agent-system-design-patterns-langgraph-b92e934bf843

[2] openlayer.com — https://openlayer.com/blog/post/multi-agent-system-architecture-guide

[3] arxiv.org — https://arxiv.org/html/2508.12683

[4] www.comet.com — https://www.comet.com/site/blog/multi-agent-systems/

[5] www.augmentcode.com — https://www.augmentcode.com/guides/multi-agent-ai-architecture-patterns-enterprise

[6] neurips.cc — https://neurips.cc/virtual/2024/poster/93363

[7] openreview.net — https://openreview.net/forum?id=cfL8zApofK

[8] aclanthology.org — https://aclanthology.org/2025.findings-acl.606.pdf

[9] www.researchgate.net — https://www.researchgate.net/publication/397203308_Multi-LLM_Debate_Framework_Principals_and_Interventions

[10] www.nature.com — https://www.nature.com/articles/s41746-026-02443-6

[11] towardsdatascience.com — https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/

[12] www.zartis.com — https://www.zartis.com/the-compounding-errors-problem-why-multi-agent-systems-fail-and-the-architecture-that-fixes-it/

[13] repository.kaust.edu.sa — https://repository.kaust.edu.sa/server/api/core/bitstreams/314fe81f-cfa1-4d93-8262-c1cde761c754/content

[14] dl.acm.org — https://dl.acm.org/doi/full/10.1145/3784013.3784018

[15] www.scribd.com — https://www.scribd.com/document/929175913/LLM-Multi-Agent-Systems-Challenges-and-Open-Problems

[16] galileo.ai — https://galileo.ai/blog/architectures-for-multi-agent-systems

[17] www.preprints.org — https://www.preprints.org/manuscript/202602.0689


## Research Process

- Total steps: 6

- Termination reason: COVERAGE_MET

- Sub-questions: 5 total, 5 covered

- Claim groups: 14

- Step results: DEAD_END, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE
