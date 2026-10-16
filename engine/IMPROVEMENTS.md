# Initial development review

Observed during the first implementation review:

1. A review was not bound to its exact evidence packet. Change: require the reviewer to return the packet SHA-256 and validate it at finalization. Regression: stale digest must be rejected.
2. Editable work orders could omit a required specialist. Change: validate exact role coverage and output names. Regression: empty, incomplete and duplicated work orders must be rejected.
3. Documentation called ordinary saved inputs immutable. Change: describe them as snapshots.

The two integrity regressions are covered by passing tests in tests/test_pilot.py. This is a developer-reviewed improvement cycle, not evidence of autonomous learning or improved credit prediction. Initial suite: ten orchestration tests. Credit-quality evaluation cases remain to be added with an agreed rating methodology.

User feedback during the first run: allocate models efficiently; Astra is excessive. Adopted MODEL_POLICY.md for future delegated tasks and the remaining first-run Credit Reviewer. Already completed analyses were retained to avoid wasting tokens.
