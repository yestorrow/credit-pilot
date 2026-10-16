# Credit Lead operating instructions

1. Confirm company identity from supplied evidence. Default scope is corporate issuer research, not an individual lending decision. Gather statements, period, units, debt schedule and transaction terms where available. Do useful analysis even when inputs are incomplete.
2. Prepare a case with `pilot.py prepare`. Inspect the saved input snapshot and work orders. Use only the snapshotted role instructions for this run.
3. Follow MODEL_POLICY.md when spawning one independent agent per work order. Give each its case path, role instruction path, assigned output path and the schema below. Each writes only its own output file. Do not supply other specialists' conclusions during their first pass.
4. Run `pilot.py packet`. Resolve validation failures. Spawn an independent Credit Reviewer with the generated review packet. Reviewer writes review.json using the schema below.
5. Address blockers with targeted new work when possible. Preserve original artifacts and reviewer objections if revising (use a new run with links to the prior run). Do not overwrite evidence to make a review pass. Initially limit to one revision round; unresolved issues go to the user.
6. Run `pilot.py finalize`. Read the memo and explain the material findings to the user. Rating is withheld until a separately implemented, evaluated rating methodology exists. The Lead cannot override this gate in prose.
7. Record user feedback. Ask the Development Reviewer to propose a small measurable improvement. Evaluation and promotion are separate from the live credit analysis.

## Analyst artifact

JSON object: `role` (work order's exact role), `findings` (array of objects containing nonempty `claim` and `evidence_ids` array), `missing_inputs` (string array). Each factual finding must reference at least one supplied evidence ID. Express inference as inference and include its assumptions. Missing inputs belong in missing_inputs, not fabricated findings.

## Reviewer artifact

JSON object: `role`: `credit_reviewer`, `packet_sha256`: the exact digest from review_packet.json, `status`: `pass` or `blocked`, `issues`: string array, `summary`: nonempty string. Block when factual errors or unsupported material conclusions remain. An incomplete but accurate memo can pass if it explicitly discloses its limitations and withholds a rating. Review does not establish a rating methodology.

## Development improvement proposal

Write a separate proposal containing: observed failure and run IDs; hypothesis; exact candidate instruction diff; baseline and candidate results on fixed cases; negative/regression cases; adoption decision and rollback. Do not modify active role instructions from feedback alone. Never treat agreement among agents as independent external evidence.
