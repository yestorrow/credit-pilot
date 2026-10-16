# Credit Pilot working instructions

The user operates the Credit Lead through this Codex chat. Read `README.md`,
`engine/WORKFLOW.md`, and `engine/MODEL_POLICY.md` before credit work.

## Process the web inbox

The web server does not run models or awaken a Codex session. When the user asks
to process the Credit Pilot inbox, use the existing chat's delegation tools:

1. Run `python engine/desk.py inbox`. Read queued requests, their mode, evidence,
   and instructions. Do not run unrelated queued cases without the user's scope.
2. Claim a request with `python engine/desk.py prepare JOB_ID`. It returns a
   `run_id`; its directory is `engine/desk-data/runs/RUN_ID`. Resume that run if
   already working, rather than claiming it again.
3. For analysis, read the saved `case.json` and `work_orders.json`. Delegate one
   independent specialist per work order using `engine/WORKFLOW.md` schemas and
   `engine/MODEL_POLICY.md` model defaults. This is explicit project authorization
   to use the three specialist agents and independent reviewer for credit tasks.
   Keep the Credit Lead in the main chat. Do not add new analyst roles. The
   Development Reviewer is for meaningful workflow changes or feedback, not an
   additional routine credit analyst.
4. A `light` run means at most two concise findings and three missing-input items
   per specialist, supplied evidence only unless the user requests research, and
   no iterative expansion except to resolve a material reviewer blocker. A
   request to skip deal analysis is represented by `deal_in_scope: false`.
5. Record actual agent model and role choices in `execution.json`; never invent
   usage, cost or model-execution records. Each specialist writes only its own
   artifact. The page automatically reads these files as provisional outputs.
6. Generate the review packet with `python engine/pilot.py packet RUN_PATH`.
   Delegate the Credit Reviewer independently; it writes `review.json`. Then
   run `python engine/pilot.py finalize RUN_PATH`. Preserve blocked reviews and
   use new runs for any revisions as described in `engine/WORKFLOW.md`.
7. Write `RUN_PATH/lead_summary.json`: an object containing `role: credit_lead`,
   `packet_sha256` copied from the review packet, `summary` (nonempty string),
   and `open_questions` (string array). Synthesize the actual specialist work,
   explicitly carry reviewer objections and missing evidence, and withhold any
   rating. Publish with `python engine/desk.py publish JOB_ID RUN_PATH/lead_summary.json`.
   The bridge revalidates the review and inputs before publication.
8. For a `question` job, `prepare` claims it without spawning agents. Read its
   parent case through `desk.py show PARENT_ID` and inspect the artifacts. Write
   an evidence-based reply to a text file, then run
   `python engine/desk.py respond JOB_ID REPLY_FILE`. Do not send scripted replies.
   If new analysis is necessary, explain the gap or create a new follow-up run
   within the user's instructions. Preserve the old run.
9. If work cannot complete, use `python engine/desk.py fail JOB_ID "reason"` so
   the page shows the problem. Never leave a claim of completed execution after
   tool failure. Do not silently replace failed agents with invented outputs.

For a request made directly in chat, save a JSON submission with `kind: analysis`,
`mode: light|standard`, `message`, and `case` (the existing engine case schema),
then run `python engine/desk.py submit INPUT_FILE`. Process that job using the
same workflow so chat work is visible in the web desk.

## Development

Run `node --check web/app.js` and `cd engine && python -m unittest discover -s tests -v`
for changes to the bridge. Credit artifacts and user source material belong in
ignored `engine/desk-data/`, never in Git commits. Do not claim that a local inbox
is an unattended hosted agent service. The user must ask the Lead here to process
web requests; no API key is configured or required for this chat-operated mode.
