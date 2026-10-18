# Credit Pilot — start here

Updated: 2026-10-18. This file is the project recap; chat history is supporting context.

## Current checkpoint

- Goal: a production credit-research tool, developed and operated from a phone.
- Working implementation: `codex/connect-credit-lead`, [draft PR #1](https://github.com/yestorrow/credit-pilot/pull/1).
- `main` still contains the earlier prototype. PR #1 is open, not merged as of this checkpoint.
- Implemented: persistent local inbox; chat-operated Lead delegation; separate analyst results; review gates; Lead synthesis; question/follow-up records; HTML interface.
- Verified: 20 Python tests and JavaScript syntax; actual fictional and super-light CATL agent runs completed. CATL used selected FY2025 disclosures, not a current full assessment.
- Incomplete: live browser verification, accessible hosted web desk, unattended model worker, shared durable storage, document ingestion, customization profile, and evaluated rating methodology.
- Blocker: local server socket creation was denied in this environment; permission-enabled attempts were interrupted. Downloaded HTML results work without a server. This does not establish that hosting elsewhere is blocked.
- Data location: source text, case artifacts and generated reports are in ignored local directories. They are not in Git and may not follow a new chat/environment. Demo completion is recorded here; its artifacts are not a durable production archive.

## What happens now

You → Credit Lead in Codex → Financial + Industry/Business + Deal analysts → independent Credit Reviewer → Lead synthesis → saved results/web desk.

The page does not wake Codex or run models automatically. Requests wait until the Lead in chat processes the inbox. Ratings are withheld. See [architecture](docs/ARCHITECTURE.md) and [experiments](docs/EXPERIMENTS.md).

## Proposed next milestones

These are recommendations, not implemented features or fixed delivery dates.

| Order | Deliverable | Completion evidence |
| --- | --- | --- |
| 1 | Establish a reproducible baseline | Review PR #1, finish browser verification on an allowed runtime, merge when authorized, and reproduce one light case from another chat. |
| 2 | Preferences/profile setup | Capture report language, sections, length, audience and units in a versioned profile; snapshot it per run; demonstrate two layouts from one unchanged evidence packet. |
| 3 | Measured context and review loop | Use fixed evidence cases and bounded retries; compare one change at a time; retain reviewer objections and actual usage records where available. |
| 4 | Hosted private pilot | Accessible mobile URL, authentication, durable case/document storage, configured model worker, job status, recovery, timeout and spend limits. A request runs without a manual chat handoff. |
| 5 | Production evaluation and release | Document ingestion/provenance, domain review, confidentiality controls, monitoring, regression evaluations, backups and recovery demonstrated. Formal ratings require a separately chosen and evaluated methodology. |

Immediate recommendation: complete the baseline, then implement the preferences profile. Hosting and private durable storage should precede confidential customer cases.

## Preferences agent proposal

Add a **Preferences/Requirements agent**, invoked when preferences change, rather than another analyst on every case. It produces a proposed profile containing language, report sections, audience, length, units and analytical scope. Save the confirmed profile once and reuse it. It may ask concise questions when a material preference is unclear.

Presentation preferences cannot suppress missing inputs, reviewer objections or evidence dates. Analytical requirements and methodology changes must be versioned separately from presentation changes. No silent edits to active prompts based on feedback.

The current Credit Lead, three analysts and independent reviewer stay intact. The Development Reviewer remains an occasional workflow-evaluation role. No preferences agent has been implemented yet.

## Model routing recommendation

| Work | Default | Escalation |
| --- | --- | --- |
| Preferences capture and routine extraction | Luna | Sol for ambiguous or conflicting requirements |
| Financial, industry/business, deal specialists | Luna | Sol for a specific failed or materially ambiguous task |
| Lead coordination, synthesis, independent review | Sol | Astra for unresolved high-complexity reasoning with user authorization |
| Routine coding | Sol | Astra for architecture/security reasoning or difficult persistent failures |
| Formatting, arithmetic, schema validation | Deterministic code | Model only for interpreting ambiguous inputs |

These are session model names, not a guarantee that identical API IDs are available in a production account. Current executable model defaults remain in `engine/MODEL_POLICY.md`. Record actual usage; do not infer savings from model names. Keep light cases to two findings and three missing-input items per specialist, with at most one revision round.

## Working from multiple phone chats

Use one coordinator chat for scope and integration. Start a focused new chat per development task or company case. Use one branch and draft PR per coding task, based on an explicit commit. Parallel tasks need separate checkouts/worktrees if they share a filesystem; branch names alone do not isolate files. Keep overlapping edits sequential. Let the coordinator integrate reviewed PRs one at a time.

The same Git repository does not imply shared conversation history, identical checked-out code, shared ignored case files, shared processes, or identical credentials.

Start a coding chat with:

> Continue Credit Pilot. Read PROJECT.md and AGENTS.md if present. Check current main and PR state. Task: [one task]. Start from [branch/commit], use a new branch, and make a draft PR. Preserve unrelated work. End with changes, checks, blockers, branch/PR and the next action.

Start a research chat with:

> Act as Credit Lead for [company]. Read PROJECT.md, AGENTS.md and engine/WORKFLOW.md. Mode: light. Use [specified sources/date]. Save this as a new case and preserve separate agent outputs. State where artifacts are stored and whether this chat can access the shared case store.

## Handoff and update rule

At task completion, record: branch/PR, what changed, checks performed, remaining blockers, artifact location and next action. A worker includes this in its PR; the coordinator updates this recap after integration. Keep customer source text, credentials and private results out of repository documentation. This repository is currently public.

## Decision record

- 2026-10-16: keep the Lead in Codex for the prototype; no unattended website dispatch or validated rating methodology.
- 2026-10-16: Luna specialists, Sol independent review; the actual CATL demo used that routing.
- 2026-10-18: user goals include production use, customization, context/loop experiments and phone-first work. Proposed sequence and preferences agent are documented above; implementation has not started.
