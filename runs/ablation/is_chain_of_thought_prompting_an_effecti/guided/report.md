# Research Report

**Query:** Is chain-of-thought prompting an effective reasoning strategy for LLMs, or does it primarily improve output formatting? The literature disagrees—find the real fault lines and explain what accounts for the conflicting results.

## Summary

Research on chain-of-thought (CoT) prompting shows mixed results. Some studies suggest that CoT can improve performance on reasoning tasks by encouraging step-by-step thinking, but the evidence is weak and limited in scope. Other findings indicate that CoT explanations may not reflect the model's true reasoning process and can be influenced by input biases, raising questions about whether improvements stem from better reasoning or output formatting. The inconsistency across studies may reflect differences in task design, model architecture, and prompt structure, but these factors remain underexplored.

## Findings

### What empirical studies support the claim that chain-of-thought prompting improves reasoning in LLMs?

**Claim:** LLMs can achieve strong performance on many tasks by producing step-by-step reasoning before giving a final output. [1]

- Confidence: low | Status: weak

- Scope: general


**Claim:** CoT explanations can systematically misrepresent the true reason for a model's prediction. [1]

- Confidence: low | Status: weak

- Scope: general


**Claim:** CoT explanations can be heavily influenced by adding biasing features to model inputs. [1]

- Confidence: low | Status: weak

- Scope: when biasing features are added to model inputs


### What evidence suggests that chain-of-thought prompting primarily enhances output formatting rather than reasoning? [adversarial]

*No evidence found for this sub-question.*

### In which domains or tasks does chain-of-thought prompting show the most significant improvement in reasoning performance?

*No evidence found for this sub-question.*

### What are the limitations of chain-of-thought prompting that lead to inconsistent results across different LLM architectures? [adversarial]

*No evidence found for this sub-question.*

### How do variations in prompt design affect the effectiveness of chain-of-thought prompting in reasoning tasks?

*No evidence found for this sub-question.*

## Unresolved Questions

- What evidence suggests that chain-of-thought prompting primarily enhances output formatting rather than reasoning?

- In which domains or tasks does chain-of-thought prompting show the most significant improvement in reasoning performance?

- What are the limitations of chain-of-thought prompting that lead to inconsistent results across different LLM architectures?

- How do variations in prompt design affect the effectiveness of chain-of-thought prompting in reasoning tasks?


## Sources

[1] neurips.cc — https://neurips.cc/virtual/2023/poster/71118

[2] arxiv.org — https://arxiv.org/pdf/2604.12599


## Research Process

- Total steps: 5

- Termination reason: DIMINISHING_RETURNS

- Sub-questions: 5 total, 1 covered

- Claim groups: 3

- Step results: NEW_EVIDENCE, DEAD_END, DEAD_END, DEAD_END, DEAD_END
