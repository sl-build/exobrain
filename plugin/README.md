# Exocortex Hermes Plugin (optional, experimental)

> **Version:** matches exocortex (currently v0.2.0)
> **Not included in the exocortex pip package.** Installed separately via Hermes Agent.

## Installation

```bash
Copy plugin.yaml to the Hermes agent skills directory
cp plugin/brain-tool/plugin.yaml ~/.hermes/skills/
```

## Plugin tools

| Tool | Purpose |
|-----------|------------|
| `brain_think` | Run reasoning via Exocortex CLI |
| `brain_plan_done` | Mark plan step complete |
| `brain_plan_block` | Block a plan step |
| `brain_plan_status` | Show plan status |

## Brain Gate

Gate protects against cyclic calls. It blocks `exocortex think` if exocortex itself called an agent that called exocortex. See `exocortex plan --block` / `--mark-done`.

## Dependencies

- exocortex CLI v0.2.0+ (`pip install exocortex`)
- Hermes Agent
