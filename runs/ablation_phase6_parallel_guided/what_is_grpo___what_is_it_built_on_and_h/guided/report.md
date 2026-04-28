# Research Report

**Query:** What is GRPO ? What is it built on and how does it work?

## Summary

GRPO (Group Relative Policy Optimization) is a variant of policy gradient reinforcement learning built on Proximal Policy Optimization (PPO) that removes the need for a separate value network by sampling multiple responses per prompt and using a simpler objective function. Research suggests GRPO achieves stronger performance with fewer computational resources and reduced memory overhead compared to standard RL methods like PPO. However, evidence also indicates that GRPO can reinforce sub-optimal behavior, and when integrated with preference models (WS-GRPO), it may incorrectly amplify trajectories that are wrongly ranked higher, with limited analysis available on failure cases.

## Findings

### What are the foundational algorithms that GRPO (Group Relative Policy Optimization) is built upon?

**Claim:** GRPO is a variant of policy gradient RL [1]

- Confidence: low | Status: weak

- Scope: GRPO


**Claim:** Group Relative Policy Optimization (GRPO) is a variant of Proximal Policy Optimization (PPO) [2]

- Confidence: low | Status: weak

- Scope: general algorithm design


### How does GRPO work technically in reinforcement learning compared to PPO?

**Claim:** GRPO removes the need for a separate value network in large language models [5]

- Confidence: low | Status: weak

- Scope: in large language models


**Claim:** PPO relies on value networks to stabilize rewards [2]

- Confidence: low | Status: weak

- Scope: in comparison with GRPO for reinforcement learning


**Claim:** GRPO samples multiple responses (rollouts) per prompt [2]

- Confidence: low | Status: weak

- Scope: GRPO's approach to training


**Claim:** The GRPO objective function is simpler and more streamlined compared to PPO. [7]

- Confidence: low | Status: weak

- Scope: when comparing GRPO and PPO training processes


### What are the computational advantages and efficiency improvements of GRPO over standard reinforcement learning methods?

**Claim:** GRPO achieves stronger performance using fewer resources in real-world scenarios. [9]

- Confidence: low | Status: weak

- Scope: in real-world scenarios


**Claim:** GRPO performs better than PPO in terms of per-step performance in reinforcement learning environments. [6]

- Confidence: low | Status: weak

- Scope: in the experiments conducted


**Claim:** GRPO significantly reduces memory and computational overhead. [10]

- Confidence: low | Status: weak

- Scope: In language model training contexts


### What are the limitations and criticisms of GRPO in training large language models? [adversarial]

**Claim:** The standard GRPO formulation can reinforce sub-optimal behavior [2]

- Confidence: low | Status: weak

- Scope: for standard GRPO formulation


### When does GRPO fail or underperform compared to alternatives like PPO or DPO? [adversarial]

**Claim:** The agent fails to learn an optimal strategy efficiently [13]

- Confidence: low | Status: weak

- Scope: based on observed oscillating low total rewards


**Claim:** The paper provides no analysis on failure cases. [14]

- Confidence: low | Status: weak

- Scope: in the paper's methodology


**Claim:** When preference model ranks wrong trajectories higher, WS-GRPO will wrongly amplify their probability. [14]

- Confidence: low | Status: weak

- Scope: when the preference model produces incorrect rankings


## Sources

[1] towardsdatascience.com — https://towardsdatascience.com/demystifying-policy-optimization-in-rl-an-introduction-to-ppo-and-grpo/

[2] arxiv.org — https://arxiv.org/abs/2402.03300

[3] www.interconnects.ai — https://www.interconnects.ai/p/papers-im-reading-base-model-rl-grpo

[4] www.emergentmind.com — https://www.emergentmind.com/topics/proximal-and-group-relative-policy-optimization

[5] huggingface.co — https://huggingface.co/blog/NormalUhr/grpo

[6] bnaic2025.unamur.be — https://bnaic2025.unamur.be/accepted-submissions/accepted_poster/061%20-%20A%20comparison%20of%20GRPO%20and%20PPO%20in%20Reinforcement%20Learning%20Environments.pdf

[7] sulbhajain.medium.com — https://sulbhajain.medium.com/proximal-policy-optimization-ppo-vs-group-relative-policy-optimization-grpo-988fa7af0241

[8] www.alexthorpe.com — https://www.alexthorpe.com/notebook/6ei2ixuu9if5mhfkohitl6mj9p95e4

[9] company.hpc-ai.com — https://company.hpc-ai.com/blog/grpo-vs-other-rl-algorithms-a-simple-clear-guide

[10] neurips.cc — https://neurips.cc/virtual/2025/poster/117119

[11] leloykun.github.io — https://leloykun.github.io/ponder/grpo-flaw/

[12] tldr.takara.ai — https://tldr.takara.ai/p/2512.04220

[13] adiinsightsinnovations.medium.com — https://adiinsightsinnovations.medium.com/mastering-llm-fine-tuning-grpo-ppo-and-dpo-compared-e362257d4036

[14] openreview.net — https://openreview.net/forum?id=rXma48njj6


## Research Process

- Total steps: 5

- Termination reason: COVERAGE_MET

- Sub-questions: 5 total, 5 covered

- Claim groups: 13

- Step results: NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE, NEW_EVIDENCE
