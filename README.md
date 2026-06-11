# Exocortex CLI v0.2.0 — Reasoning Engine for AI Agents

[![PyPI version](https://img.shields.io/pypi/v/exocortex)](https://pypi.org/project/exocortex/)

Exocortex CLI is an exocortex for AI agents. It sends prompts to reasoning models (OpenAI, Anthropic, Gemini, DeepSeek, Qwen) via OpenRouter and returns the response. Can be used as an MCP tool or standalone.

## Quick Start

```bash
pip install exocortex
export OPENROUTER_API_KEY=sk-or-...
exocortex think "How does async/await work in Python?"
```

## Usage

- `exocortex think "prompt"` — basic
- `exocortex think "prompt" --model gpt-4o --depth high` — with model and depth
- `exocortex think "prompt" --context "context"` — with context
- `exocortex think "prompt" --context-file file.txt` — from file
- `cat log.txt | exocortex think "why?" --stdin-context` — from stdin
- `exocortex think "prompt" --json` — JSON response
- `exocortex think "prompt" --stats` — with stats
- `exocortex think "prompt" --plan` — planning mode
- `exocortex think "prompt" --session-id my-session` — multi-session

## Plan Management

- `exocortex plan` — show plan
- `exocortex plan --mark-done` — mark step done
- `exocortex plan --block` — block step

## Provider

Default is OpenRouter (300+ models). Can be switched:

```bash
exocortex config-set --provider opencode_go
exocortex config-set --provider openrouter
```

## Profiles

Six built-in profiles: reasoning, writer, planner, critic, research, creative.

Custom profiles:

```bash
exocortex profile-add my-profile template=reasoning model=qwen-max-0125
exocortex profiles
exocortex profile-remove my-profile
```

## Depth presets

- `low` — fast, shallow
- `medium` (default) — balanced
- `high` — deep reasoning

## Hermes Plugin (optional, experimental)

Exocortex CLI can be connected to a Hermes agent. See plugin/README.md.

The plugin registers Hermes tool identifiers (`brain_think`, `brain_plan_done`, etc.) that remain unchanged for compatibility with existing agent configurations.

Note: not included in the pip package; installed separately.

## Install

```bash
pip install exocortex
```

For Hermes Agent: `pip install exocortex hermes` (plugin not included, see plugin/README.md)

## Requirements

Python 3.11+, API key from OpenRouter (openrouter.ai/keys)

## License

MIT
