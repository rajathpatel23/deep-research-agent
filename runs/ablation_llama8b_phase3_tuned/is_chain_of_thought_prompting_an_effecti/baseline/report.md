# Research Report

**Query:** Is chain-of-thought prompting an effective reasoning strategy for LLMs, or does it primarily improve output formatting? The literature disagrees—find the real fault lines and explain what accounts for the conflicting results.

## Summary

Our research findings suggest that chain-of-thought prompting may have a mixed impact on large language models' (LLMs) reasoning abilities. While it appears to be effective in certain simple language generation tasks or those with low cognitive demands, its benefits may be largely related to output formatting improvements rather than genuine reasoning enhancements. However, the existing literature is limited, and potential biases in task selection, evaluation metrics, or experimental design may be contributing to the conflicting results, which warrants further investigation.

## Findings

### What are the specific reasoning tasks where chain-of-thought prompting consistently demonstrates significant improvement in LLMs' performance compared to non-chain-of-thought methods?

**Claim:** Chain of thought has been proven super useful in many reasoning tasks [4]

- Confidence: low | Status: weak

- Scope: reasoning tasks


**Claim:** Chain of thought prompting: few-shot, zero-shot, and many many follow-up works [4]

- Confidence: low | Status: weak

- Scope: chain of thought prompting


### Do studies using simple language generation tasks or those with low cognitive demands find chain-of-thought prompting to be more effective than formatting-focused improvements, and why?

**Claim:** Chain of thought has been proven super useful in many reasoning tasks [4]

- Confidence: low | Status: weak


**Claim:** This work achieves new state-of-the-art (SOTA) performance [5]

- Confidence: low | Status: weak

- Scope: on three math benchmarks and two BigBenchHard tasks


**Claim:** The effectiveness of Chain-of-thought prompting has been widely recognized. [14]

- Confidence: low | Status: weak

- Scope: for a wide range of tasks


**Claim:** generating a chain of thought improves the ability of large language models to perform complex reasoning [7]

- Confidence: low | Status: weak

- Scope: for large language models


### Can chain-of-thought prompting exacerbate the known issue of LLMs' overreliance on statistical patterns rather than genuine reasoning, and what are the implications for downstream applications? [adversarial]

**Claim:** Large language models benefit from chain-of-thought prompting [19]

- Confidence: low | Status: weak

- Scope: for large language models


**Claim:** BadChain is a novel backdoor attack targeting large language models [19]

- Confidence: low | Status: weak

- Scope: for large language models


### Are there specific LLM architectures or training protocols that are more susceptible to chain-of-thought prompting's limitations in improving actual reasoning abilities, and what design choices contribute to these vulnerabilities? [adversarial]

**Claim:** This work proposes contrastive chain of thought, an automatic method to construct contrastive demonstrations that provides both valid and invalid reasoning demonstrations. [16]

- Confidence: low | Status: weak

- Scope: to guide the model to reason step-by-step while reducing reasoning mistakes


### What are the potential biases in the existing literature on chain-of-thought prompting that might be driving the conflicting results, such as differences in task selection, evaluation metrics, or experimental design? [adversarial]

*No evidence found for this sub-question.*

## Unresolved Questions

- What are the potential biases in the existing literature on chain-of-thought prompting that might be driving the conflicting results, such as differences in task selection, evaluation metrics, or experimental design?


## Sources

[1] iafor.org — https://iafor.org/archives/conference-programmes/aceid/aceid-programme-2026.pdf

[2] ceramics.org — https://ceramics.org/wp-content/uploads/2026/03/3.23.SPRING26_Abstracts-3-002.pdf

[3] arxiv.org — https://arxiv.org/pdf/2512.23941

[4] neurips.cc — https://neurips.cc/media/neurips-2024/Slides/96654.pdf

[5] api.semanticscholar.org — https://api.semanticscholar.org/arXiv:2210.00720

[6] www.ibm.com — https://www.ibm.com/think/topics/chain-of-thoughts

[7] openreview.net — https://openreview.net/forum?id=va7nzRsbA4

[8] www.sciencedirect.com — https://www.sciencedirect.com/science/article/abs/pii/S0957417426004240

[9] www.linkedin.com — https://www.linkedin.com/pulse/chain-of-thought-prompting-my-take-paper-changed-how-i-pallikala-ooxic

[10] dl.acm.org — https://dl.acm.org/doi/proceedings/10.1145/3721146

[11] violetpeng.github.io — https://violetpeng.github.io/

[12] www.cs.jhu.edu — https://www.cs.jhu.edu/department-seminars/

[13] alphaxiv.org — https://alphaxiv.org/overview/2307.13339v1

[14] aclanthology.org — https://aclanthology.org/2023.findings-emnlp.101.pdf

[15] www.researchgate.net — https://www.researchgate.net/publication/395944412_Why_Chain_of_Thought_Fails_in_Clinical_Text_Understanding

[16] www.semanticscholar.org — https://www.semanticscholar.org/paper/Contrastive-Chain-of-Thought-Prompting-Chia-Chen/11b95e33f1a61079105e06090984b9dd8742887e

[17] papers.ssrn.com — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5285532

[18] www.lesswrong.com — https://www.lesswrong.com/posts/37sdqP7GcfGaj6LHG/the-decreasing-value-of-chain-of-thought-in-prompting

[19] huggingface.co — https://huggingface.co/papers/2401.12242

[20] proceedings.neurips.cc — https://proceedings.neurips.cc/paper_files/paper/2024/file/00d80722b756de0166523a87805dd00f-Paper-Conference.pdf

[21] www.arxiv.org — https://www.arxiv.org/pdf/2506.17088v2


## Research Process

- Total steps: 15

- Termination reason: BUDGET_EXHAUSTED

- Sub-questions: 5 total, 4 covered

- Claim groups: 9

- Step results: DEAD_END, NEW_EVIDENCE, DEAD_END, NO_EXTRACTABLE_CLAIMS, DEAD_END, NO_EXTRACTABLE_CLAIMS, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, DEAD_END, NEW_EVIDENCE, DEAD_END, DEAD_END
