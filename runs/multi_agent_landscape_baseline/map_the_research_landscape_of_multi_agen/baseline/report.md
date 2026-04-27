# Research Report

**Query:** Map the research landscape of multi-agent LLM systems. Produce a structured report that includes a visual taxonomy or design graph showing the major architectural patterns, how they relate, and where the open problems are.

## Summary

Research indicates that multi-agent LLM systems operate across several distinct architectural patterns—including sequential pipelines and parallel fan-out with merge structures—with context distributed across agents with separate windows, though systematic comparison frameworks remain nascent. Evidence points to structured taxonomies of failure modes organized into three to four functional categories, with findings suggesting that multi-agent systems often yield minimal performance improvements on existing benchmarks, and that this appears to be among the first comprehensive investigations of multi-agent LLM challenges. Notably, the evidence leaves significant gaps regarding coordination mechanisms and communication protocols in popular frameworks like AutoGen, CrewAI, and LangGraph, representing an area where research coverage is currently insufficient.

## Findings

### What are the major architectural patterns for multi-agent LLM systems?

**Claim:** The paper presents a systematic benchmark comparing four multi-agent orchestration architectures. [2]

- Confidence: low | Status: weak

- Scope: General multi-agent orchestration evaluation


**Claim:** This work presents a systematic benchmark comparing four multi-agent orchestration architectures: sequential pipeline, parallel fan-out with merge, ... [2]

- Confidence: low | Status: weak

- Scope: Not specified


**Claim:** Multi-agent architectures distribute context across agents with separate windows [3]

- Confidence: low | Status: weak

- Scope: in multi-agent systems


**Claim:** A systematic benchmark comparing four multi-agent orchestration architectures is presented [2]

- Confidence: low | Status: weak

- Scope: multi-agent system research


**Claim:** Sequential pipeline is one of four multi-agent orchestration architectures being benchmarked [2]

- Confidence: low | Status: weak

- Scope: multi-agent orchestration architectures


### What coordination mechanisms and communication protocols are used in multi-agent LLM frameworks like AutoGen, CrewAI, and LangGraph?

*No evidence found for this sub-question.*

### What evaluation benchmarks and metrics are used to assess multi-agent LLM system performance?

**Claim:** A systematic benchmark comparing four multi-agent orchestration architectures exists [2]

- Confidence: low | Status: weak

- Scope: for multi-agent system evaluation


**Claim:** This work aims to bring clarity to the fragmented landscape of agent evaluation and provide a framework for systematic assessment [2]

- Confidence: low | Status: weak

- Scope: agent evaluation


### What are the failure modes, limitations, and criticisms of current multi-agent LLM architectures? [adversarial]

**Claim:** This paper presents a structured taxonomy of LLM agent failure modes with formal definitions [16]

- Confidence: low | Status: weak

- Scope: LLM agent systems


**Claim:** The taxonomy of LLM agent failure modes is organized across four functional categories [16]

- Confidence: low | Status: weak

- Scope: LLM agent systems


**Claim:** The paper benchmarks and systematically explores failure modes of multi-agent systems. [7]

- Confidence: low | Status: weak

- Scope: not specified


**Claim:** This study presents the first systematic investigation of failure modes of LLM based Multi-Agent Systems [2]

- Confidence: low | Status: weak

- Scope: LLM based Multi-Agent Systems


### What are the open research problems and unsolved challenges in multi-agent LLM systems? [adversarial]

**Claim:** Fine-grained failure modes in multi-agent systems are organized into 3 categories [2]

- Confidence: low | Status: weak

- Scope: for analysis of multi-agent AI system failures


**Claim:** Multi-Agent LLM Systems often show minimal performance gains on popular benchmarks. [18]

- Confidence: low | Status: weak

- Scope: on popular benchmarks


**Claim:** This paper presents the first comprehensive study of MAS challenges [2]

- Confidence: low | Status: weak

- Scope: general (paper's stated contribution)


## Unresolved Questions

- What coordination mechanisms and communication protocols are used in multi-agent LLM frameworks like AutoGen, CrewAI, and LangGraph?


## Sources

[1] medium.com — https://medium.com/@princekrampah/multi-agent-architecture-in-multi-agent-systems-multi-agent-system-design-patterns-langgraph-b92e934bf843

[2] arxiv.org — https://arxiv.org/html/2404.04834v4

[3] galileo.ai — https://galileo.ai/blog/architectures-for-multi-agent-systems

[4] www.researchgate.net — https://www.researchgate.net/publication/384732283_A_survey_on_LLM-based_multi-agent_systems_workflow_infrastructure_and_challenges

[5] www.comet.com — https://www.comet.com/site/blog/multi-agent-systems/

[6] www.augmentcode.com — https://www.augmentcode.com/guides/multi-agent-ai-architecture-patterns-enterprise

[7] openreview.net — https://openreview.net/forum?id=fAjbYBmonr&referrer=%5Bthe%20profile%20of%20Matei%20Zaharia%5D(%2Fprofile%3Fid%3D~Matei_Zaharia1)

[8] xue-guang.com — https://xue-guang.com/post/llm-marl/

[9] aaronyuqi.medium.com — https://aaronyuqi.medium.com/first-hand-comparison-of-langgraph-crewai-and-autogen-30026e60b563

[10] dev.to — https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63

[11] www.rapidinnovation.io — https://www.rapidinnovation.io/post/a-comparative-analysis-of-langgraph-crewai-and-autogen

[12] link.springer.com — https://link.springer.com/article/10.1007/s44336-024-00009-2

[13] dl.acm.org — https://dl.acm.org/doi/10.1145/3712003

[14] orq.ai — https://orq.ai/blog/multi-agent-llm-eval-system

[15] www.llmwatch.com — https://www.llmwatch.com/p/multi-agent-failure-why-complex-ai

[16] papers.ssrn.com — https://papers.ssrn.com/sol3/Delivery.cfm/6572478.pdf?abstractid=6572478&mirid=1

[17] towardsdatascience.com — https://towardsdatascience.com/why-your-multi-agent-system-is-failing-escaping-the-17x-error-trap-of-the-bag-of-agents/

[18] neurips.cc — https://neurips.cc/virtual/2025/122442

[19] huggingface.co — https://huggingface.co/blog/Musamolla/multi-agent-llm-systems-failure

[20] github.com — https://github.com/AGI-Edgerunners/LLM-Agents-Papers

[21] redis.io — https://redis.io/blog/why-multi-agent-llm-systems-fail/

[22] openlayer.com — https://openlayer.com/blog/post/multi-agent-system-architecture-guide


## Research Process

- Total steps: 12

- Termination reason: BUDGET_EXHAUSTED

- Sub-questions: 5 total, 4 covered

- Claim groups: 14

- Step results: NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE, NEW_EVIDENCE, NO_EXTRACTABLE_CLAIMS
