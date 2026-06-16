# ExoBrain Hermes Plugin (optional, experimental)

> **Version:** matches exobrain (currently v0.2.5)
> **Not included in the exobrain pip package.** Installed separately via Hermes Agent.

## Installation

```bash
Copy plugin.yaml to the Hermes agent skills directory
cp plugin/exobrain-tool/plugin.yaml ~/.hermes/skills/
```

## Plugin tools

| Tool | Purpose |
|-----------|------------|
| `brain_think` | Run reasoning via ExoBrain CLI |
| `brain_plan_done` | Mark plan step complete |
| `brain_plan_block` | Block a plan step |
| `brain_plan_status` | Show plan status |

## Brain Gate

Gate protects against cyclic calls. It blocks `exobrain think` if exobrain itself called an agent that called exobrain. See `exobrain plan --block` / `--mark-done`.

## Dependencies

- exobrain CLI v0.2.5+ (`pip install exobrain-cli`)
- Hermes Agent
