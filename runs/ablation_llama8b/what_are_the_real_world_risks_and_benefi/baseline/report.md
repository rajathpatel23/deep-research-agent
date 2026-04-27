# Research Report

**Query:** What are the real-world risks and benefits of using synthetic data to train or fine-tune large language models? Focus on data quality, bias, and evaluation.

## Summary

Our research findings suggest that synthetic data can be effective for training large language models, particularly in computationally intensive first phases, such as pre-training Foundational Models. However, the quality of synthetic data is crucial, as poor quality data may exacerbate existing biases in large language models, including sociolinguistic biases. Furthermore, evaluation metrics and methods are needed to assess the effectiveness and reliability of synthetic data in training large language models, as current evidence indicates that large language models can produce high-quality text but differ in their usefulness.

## Findings

### What types of synthetic data are most effective for training large language models in real-world applications?

**Claim:** Large-scale pre-training of Foundational Models (FM) constitutes a computationally intensive first phase [2]

- Confidence: low | Status: weak

- Scope: for FM


### Can synthetic data mitigate or exacerbate existing biases in large language models, and how can this be evaluated? [adversarial]

**Claim:** Style-conditioned data poisoning is a covert vector for amplifying sociolinguistic bias in large language models. [2]

- Confidence: low | Status: weak

- Scope: large language models


**Claim:** Linguistic style can act as a latent trigger for harmful behavior. [2]

- Confidence: low | Status: weak

- Scope: linguistic style


**Claim:** Small-scale data poisoning can exacerbate dialect-linked biases in large language models. [2]

- Confidence: low | Status: weak

- Scope: large language models


**Claim:** Poisoned exposure elevates toxicity and stereotype expression for dialectal inputs. [2]

- Confidence: low | Status: weak

- Scope: dialectal inputs


**Claim:** AAVE dialect is associated with higher toxicity and stereotype expression compared to other dialects. [2]

- Confidence: low | Status: weak

- Scope: AAVE dialect


**Claim:** Standard American English is less susceptible to toxicity and stereotype expression compared to dialectal inputs. [2]

- Confidence: low | Status: weak

- Scope: Standard American English


**Claim:** Small poisoned budgets can amplify sociolinguistic bias in large language models. [2]

- Confidence: low | Status: weak

- Scope: large language models


**Claim:** AAVE dialectal inputs are most consistently associated with elevated toxicity and stereotype expression. [2]

- Confidence: low | Status: weak

- Scope: AAVE dialectal inputs


**Claim:** Standard American English is not immune to the effects of data poisoning. [2]

- Confidence: low | Status: weak

- Scope: Standard American English


**Claim:** Standard American English remains comparatively lower yet not immune to poisoned exposure. [2]

- Confidence: low | Status: weak

- Scope: for Standard American English


**Claim:** Poisoned exposure elevates stereotype expression for dialectal inputs, most consistently for AAVE. [2]

- Confidence: low | Status: weak

- Scope: for dialectal inputs, especially AAVE


**Claim:** AAVE dialectal inputs are most consistently affected by poisoned exposure. [2]

- Confidence: low | Status: weak

- Scope: AAVE dialectal inputs


### How does the quality of synthetic data impact the performance and generalizability of large language models in real-world scenarios?

*No evidence found for this sub-question.*

### What are the potential risks of relying on synthetic data for fine-tuning large language models, particularly in high-stakes applications like healthcare or finance? [adversarial]

*No evidence found for this sub-question.*

### What evaluation metrics and methods can be used to assess the effectiveness and reliability of synthetic data in training large language models?

**Claim:** LLMs are powerful generators of synthetic data [3]

- Confidence: low | Status: weak

- Scope: for training smaller, specific models


**Claim:** human-labelled data is scarce [3]

- Confidence: low | Status: weak

- Scope: for low-resource languages


**Claim:** LLMs can produce high-quality text [3]

- Confidence: low | Status: weak

- Scope: for low-resource languages


**Claim:** LLMs differ in how useful their outputs are [3]

- Confidence: low | Status: weak


**Claim:** We evaluate the effectiveness of synthetic data fine-tuning [3]

- Confidence: low | Status: weak

- Scope: for Semantic Search in a real-world Enterprise Team Formation problem scenario


**Claim:** we aim to retrieve the best employee for a given task [3]

- Confidence: low | Status: weak

- Scope: given their information regarding abilities, experiences, and other aspects


**Claim:** We evaluate two synthetic data fine-tuning approaches [3]

- Confidence: low | Status: weak

- Scope: not specified


## Unresolved Questions

- How does the quality of synthetic data impact the performance and generalizability of large language models in real-world scenarios?

- What are the potential risks of relying on synthetic data for fine-tuning large language models, particularly in high-stakes applications like healthcare or finance?


## Sources

[1] openreview.net — https://openreview.net/group?id=ICLR.cc/2026/Workshop/Reliable_Autonomy&referrer=%5BHomepage%5D(%2F)

[2] arxiv.org — https://arxiv.org/pdf/2604.12599

[3] aclanthology.org — https://aclanthology.org/2026.eacl-long.258.pdf


## Research Process

- Total steps: 10

- Termination reason: BUDGET_EXHAUSTED

- Sub-questions: 5 total, 3 covered

- Claim groups: 20

- Step results: NEW_EVIDENCE, NEW_EVIDENCE, DEAD_END, DEAD_END, NEW_EVIDENCE, REDUNDANT, NEW_EVIDENCE, DEAD_END, DEAD_END, REDUNDANT
