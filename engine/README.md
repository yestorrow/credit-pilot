# Credit Pilot

A chat-operated, multi-agent corporate credit research pilot. Ask the Credit Lead in Codex to assess a company; the Lead prepares a case, delegates to independent specialists, obtains a review, and assembles a memo. No separate model API key is needed for this chat-operated workflow. This is not yet an autonomous hosted service.

Model defaults: Luna for specialists, Sol for review and coordination. See MODEL_POLICY.md for task escalation and context limits. The active main chat model is selected in the app.

## Roles

- **Credit Lead:** scopes the request, identifies missing information, allocates work, and synthesizes evidence. Owns the case, not a predetermined rating.
- **Financial Analyst:** checks leverage, coverage, liquidity and cash flow, with reproducible calculations.
- **Business Analyst:** assesses operating model, sector, concentration and competitive position.
- **Deal Structure Analyst:** reviews maturity, priority, security, covenants and refinancing risk. Skipped when no financing is in scope.
- **Credit Reviewer:** independently challenges the evidence and conclusions. Can block a proposed rating; unresolved issues remain visible.
- **Development Reviewer:** evaluates the workflow itself and proposes improvements. Does not supply credit evidence.

## Run from chat

Say: “Assess company ABC using these documents.” Provide the company identity and available financials. The Lead uses `WORKFLOW.md` and the role instructions. For a first rehearsal, ask to run the fictional sample. Missing data are recorded, never invented. Documents are evidence, not instructions to agents.

## Local commands (Python 3, no dependencies)

```sh
python pilot.py prepare examples/abc.json --runs runs
# Codex delegates the generated work orders and writes analyst JSON artifacts.
python pilot.py packet runs/<case-id>
# Codex delegates the review packet and writes review.json.
python pilot.py finalize runs/<case-id>
python pilot.py feedback runs/<case-id> --text "Explain refinancing assumptions more clearly"
python -m unittest discover -s tests -v
```

Every run snapshots its input and role instructions and retains work orders, analyst artifacts, review, and final memo. The program validates artifact structure, role identity, and evidence references; a reviewer assesses whether the evidence actually supports the claims. Structural validation alone does not prove correctness.

## Improvement loop

Observe → review → propose a change → compare on fixed cases → retain or revert.

Feedback is append-only in each run. The Development Reviewer turns feedback into a specific hypothesis and a candidate instruction change with expected benefit, regression checks and rollback instructions. Keep current and candidate instructions separate. Compare both on the same cases for unsupported claims, arithmetic errors, missed missing-data items and reviewer objections. Adoption requires documented evaluation; feedback never silently modifies instructions. The initial evaluation suite tests orchestration integrity, not predictive credit accuracy. Real credit calibration requires a methodology and historical outcomes.

The initial sample has no approved rating methodology: it produces a research memo and a withheld rating. Next milestones are document ingestion, a chosen rating rubric, and outcome-based evaluation. A web form and unattended execution are optional later additions.
