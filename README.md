# Credit Pilot

A corporate credit research desk operated by the Credit Lead in Codex chat.
The lead delegates to the existing Financial Analyst, Business/Industry Analyst,
Deal Structure Analyst and independent Credit Reviewer. Deal work is skipped
when no debt or transaction is in scope. The Development Reviewer remains a
workflow-improvement role, not an extra credit analyst on each case.

## Open the web desk

Python 3 on Linux, no external packages or model API key required:

```sh
python engine/desk.py serve --port 8000
```

Open http://127.0.0.1:8000 in the browser **on the machine running the server**.
If the server runs in a cloud workspace, use that environment's authenticated
port forwarding to port 8000. This repository does not configure hosting or a
public URL. Opening `web/index.html` directly does not connect the API.

The page saves real requests to a persistent inbox and refreshes case results.
It shows the Credit Lead executive summary, each specialist's individual findings,
missing information, the independent review, evidence and the case conversation.
Provisional findings are labeled as awaiting review. Invalidated or blocked
reviews remain visible. Follow-up analysis creates a separate case run.

## Use this chat as the Credit Lead

1. Submit a company, instruction and source text in the web desk. Choose **Light
   test** for a small first run. Source text is retained as evidence; URLs alone
   are not fetched and documents are not automatically extracted.
2. In this Codex chat, say **“Process the Credit Pilot inbox.”** The Lead claims
   the job, dispatches the existing specialists, gets an independent review and
   publishes its synthesis. The page updates as artifacts arrive.
3. Ask a question in the case conversation, then ask the Lead here to process
   the inbox again. Answers are written by the Lead from the actual case data.
   Choose **Delegate follow-up analysis** to request a new reviewed run instead.

You can also give the company and source material directly to the Lead here.
It uses the same persisted workflow so the results appear on the page. Operator
instructions and commands are in `AGENTS.md`.

**Execution model:** the local server stores requests and serves results. It
never calls models, spawns Codex agents, or wakes this chat automatically. The
Credit Lead uses this chat's agent tools to delegate when asked. Unattended web
execution would need a separately configured model worker and credentials; it
is not enabled by this setup. There are no scripted chat replies in the desk.

## Light runs

At most two concise findings and three missing inputs per specialist, supplied
source evidence only unless external research is requested, and a brief
independent review. No real company is analyzed until the user selects one.
Use `engine/examples/abc.json` for a clearly fictional connection check.

Ratings remain withheld: no validated rating methodology is implemented. A
passed review validates a limited research memo, not a calibrated credit rating.
Missing evidence and reviewer objections stay visible in the output.

## Development and checks

- `engine/pilot.py`: snapshots, work orders, validation, review packets and memos.
- `engine/desk.py`: persistent inbox, publication and local HTTP API.
- `web/`: buildless HTML, CSS and JavaScript with live result polling.
- `engine/roles/`: fixed specialist and reviewer instructions.
- `engine/desk-data/`: ignored local requests, evidence, conversations and results.

```sh
node --check web/app.js
cd engine
python -m unittest discover -s tests -v
```

Model defaults and escalation are in `engine/MODEL_POLICY.md`: Luna specialists,
Sol review and coordination. Actual platform model IDs depend on the session.
The engine records artifacts, not fabricated usage or cost data. See
`engine/WORKFLOW.md` for review gates and `engine/IMPROVEMENTS.md` for the feedback
process. Future work includes document ingestion, an evaluated rating rubric,
and an optional unattended worker.
