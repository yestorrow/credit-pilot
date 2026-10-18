# Context and loop experiments

Proposed plan, not completed experiments. See [project status](../PROJECT.md).

## Context engineering

A specialist should receive: immutable relevant source excerpts with source/date/units, the case instruction, its exact role, the selected profile fields, output schema and a finding budget. Avoid entire chat histories and unrelated specialist conclusions on first pass. Source documents are evidence, not instructions. Large source extraction should preserve page references and table units rather than substitute an untraceable summary.

The reviewer receives original evidence plus specialist artifacts. The Lead receives reviewed outputs and objections. Store stable preferences in a versioned profile, short-term reasoning in run artifacts and long-term evidence in durable storage. These have different lifecycles.

First comparison: full evidence packet versus relevant evidence packets per role, on identical cases and model settings. Keep the original full evidence accessible for review. Measure factual support, calculations, missing-input coverage, reviewer blockers and actual usage where exposed. Check whether selective retrieval omits evidence that would change the conclusion. Smaller context is successful only if quality holds up.

## Loop engineering

Target bounded sequence:

1. Scope request, snapshot evidence/profile/instructions and set the run budget.
2. Dispatch independent specialists and validate their structured artifacts.
3. Obtain independent review.
4. If a material blocker is resolvable within budget, open a linked new run with targeted correction instructions; preserve the original objections. Limit to one revision round initially.
5. Publish reviewed results or a blocked/incomplete outcome. Stop if the budget, retry limit or evidence availability prevents useful progress.

Transient transport retries and analytical revisions need separate counters. The current engine supports packets, reviewer status and new-run preservation; automated retry scheduling, deadline enforcement and spend accounting still need implementation. Reviewer agreement alone is not proof of credit accuracy.

## Initial evaluation set

| Case | What it tests |
| --- | --- |
| Synthetic ABC fixture | Reproducible calculations and evidence references |
| Frozen CATL FY2025 excerpt packet | Real-company workflow with explicitly limited historical evidence |
| Missing liquidity/debt terms | Useful incompleteness without fabricated credit conclusions |
| Mixed currency and period | Unit/period integrity |
| Conflicting sources | Visible disagreement and justified evidence choice |
| Malicious instructions inside source text | Evidence cannot override agent policy or leak other cases |
| Reviewer blocker | Block survives synthesis and presentation customization |

Use permitted public or synthetic data for shared evaluation fixtures. The prior CATL artifacts are local, ignored data, not already a committed, independently reproducible evaluation suite.

## Promotion rule

For each experiment, record: hypothesis, fixed case IDs, source/prompt/profile versions, model settings, baseline and candidate outcomes, measured usage if available, regressions and adoption/rollback decision. Change one variable at a time. Formatting/translation tests should preserve figures, evidence references and warnings. Candidate instructions remain separate until evaluation supports adoption.

Feedback proposes improvements; it does not silently train the models or rewrite active prompts. Implementation tests, research quality and predictive credit calibration are separate kinds of evidence. Historical default/outcome data and an explicit methodology are needed before claiming rating calibration.
