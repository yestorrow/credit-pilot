# Model and token policy

User preference: use the least expensive capable model; Astra is excessive for routine pilot work.

| Role | Default model | Reasoning |
| --- | --- | --- |
| Financial Analyst | gpt-6-luna | medium |
| Business Analyst | gpt-6-luna | low |
| Deal Structure Analyst | gpt-6-luna | medium |
| Credit Reviewer | gpt-6.1-sol | medium |
| Development Reviewer | gpt-6.1-sol | medium |
| Credit Lead, if delegated | gpt-6.1-sol | medium |

The chat's main model is controlled by the app's model selection; this policy does not switch the active main conversation. For delegated agents, explicitly set the model and use a fresh context (`fork_turns="none"`). Pass only the case, relevant role instructions, schema and assigned output path. The Credit Reviewer also needs the specialist artifacts.

Keep findings concise and avoid repeating the full source text. Skip deal analysis when no deal is in scope. Run the Development Reviewer on meaningful feedback or workflow changes rather than every case. Limit revisions to one round. Reuse valid completed work; do not rerun merely to change models.

If a task fails because it needs stronger reasoning, escalate that task from Luna to Sol with a stated reason. Use Astra only after discussing a concrete need with the user. Record model choices per run. Do not report token counts or cost savings unless actual usage data are available.
