# Credit Pilot

A mobile-first prototype for multi-agent corporate credit research, developed in Codex.

## Project layout

- `engine/`: Python work-packet orchestration, role instructions, model policy and tests.
- `web/`: buildless HTML/CSS/JavaScript interface with executive summary, industry analysis, financial analysis, deal review and a demo Credit Lead conversation.
- `examples/`: fictional input and completed research memo.

## View the interface

Open `web/index.html` in a browser, or serve the project:

```sh
python -m http.server 8000
```

Then visit `http://localhost:8000/web/`. Select the completed ABC case to explore the executive summary, analysts and Credit Lead conversation.

## Run the engine checks

Python 3, no external dependencies:

```sh
cd engine
python -m unittest discover -s tests -v
python pilot.py prepare examples/abc.json
```

Read `engine/WORKFLOW.md` for agent delegation and review. The engine prepares and validates artifacts; it does not itself call model APIs. Agents were executed through Codex sessions in the original pilot.

## Current scope

The web interface uses a fictional case and scripted demo responses. It is not connected to the engine or a model API. No validated credit rating methodology is implemented, so ratings are withheld. Industry content and the executive summary in the interface are prototype synthesis, not new independently reviewed analyst outputs.

## Continue in another Codex session

Connect this repository to a Codex environment and ask: “Continue Credit Pilot. Read README.md, engine/WORKFLOW.md and engine/MODEL_POLICY.md. Inspect web/ and the fictional example. Help connect the interface to a backend while preserving evidence references and independent review.”

Use Luna for routine delegated analysis and Sol for review where those models are available. Model IDs are platform-specific configuration, not dependencies of this source code.

## Next steps

Connect UI requests to a backend, add document ingestion, implement model routing, choose and evaluate a rating methodology, and add credit-quality evaluation cases. The improvement loop currently records feedback and evaluates developer-proposed changes; it is not autonomous learning.
