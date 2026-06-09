# Brain CLI

Exocortex reasoning engine for AI agents. Multi-provider LLM gateway with reasoning profiles, depth control, and structured output.

## Install

```bash
uv tool install git+https://github.com/sl-build/brain-cli.git
```

Or from source:

```bash
git clone https://github.com/sl-build/brain-cli.git
cd brain-cli
uv tool install --editable .
```

## Usage

```bash
# Quick reasoning
brain think "Should we migrate from REST to gRPC?"

# With reasoning profile
brain think "Explain quantum entanglement" --profile critic

# Depth control
brain think "Design a cache strategy" --depth deep

# JSON output (for agent pipelines)
brain think "Summarize this" --json

# Provider management
brain config                    # Show current config
brain config-set provider opencode_go  # Switch provider

# View available profiles
brain profiles
```

## Providers

| Provider | Default Model | Base URL |
|----------|--------------|----------|
| OpenRouter | `openai/gpt-5.5` | `openrouter.ai/api/v1` |
| OpenCode Go | `qwen-3.7-max` | `opencode.ai/zen/go/v1` |

Switch providers via `brain config-set provider <name>` or `--provider` flag.

## Reasoning Profiles

- **reasoning** — step-by-step analysis (default)
- **critic** — find flaws and weak points
- **planner** — structured action plans
- **judge** — balanced pros/cons evaluation
- **extractor** — pull key facts from noise

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API failure / network error |
| 2 | Bad response from model |
| 3 | Input error (bad args, missing key) |

## Context Injection

```bash
# Inline context
brain think "Is this a good deal?" --context "Price: $50, Budget: $100"

# From file
brain think "Summarize" --context-file notes.md

# From stdin
cat log.txt | brain think "Find errors" --stdin-context
```

## Config

Config stored at `~/.config/brain/config.toml`:

```toml
[defaults]
provider = "openrouter"
```

## License

MIT