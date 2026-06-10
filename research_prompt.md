# Research: OpenCode Go reasoning models API format & Python multi-provider LLM libraries

## Context

We're adding a provider abstraction layer to [brain CLI](https://github.com/anomalyco/brain-cli) — a lightweight Python CLI tool for AI agents. Currently it uses only the OpenAI SDK (`openai>=1.0.0`) and supports two providers: OpenRouter and OpenCode Go (via oa-compat).

We need to support OpenCode Go reasoning models (like `qwen3.7-max`) that do NOT support the standard `oa-compat` (OpenAI-compatible chat completions) API format. We need to understand what format they DO use.

## Questions to answer

1. **OpenCode Go reasoning API format**: What is the actual API format/endpoint for models like `qwen3.7-max` on OpenCode Go? How does Hermes (the tool at `~/.hermes/`) call these models? Look at:
   - Hermes source code (reversibly decompiled or source if available at `~/.hermes/`)
   - OpenCode Go API documentation at https://opencode.ai
   - Network traffic from Hermes to OpenCode Go when using qwen3.7-max
   - Specifically: endpoint path, request body format, authentication method, response format

2. **Python multi-provider LLM libraries**: Evaluate these options for abstracting LLM providers:
   - **LiteLLM**: How heavy is it? How many transitive dependencies? Does it support custom endpoints like OpenCode Go? Can we use only the completion part without the rest?
   - **llm (Simon Willison's)**: Same questions
   - **openai-agents-python**: Same questions
   - **Custom (no library)**: Using `httpx` or stdlib `urllib` for raw HTTP calls

3. **OpenCode Go model map**: Which models use oa-compat vs reasoning format? Is there a documented list or way to detect?

## Deliverable

A concise report covering:
- The exact request/response format for OpenCode Go reasoning models (with curl example)
- Recommendation on library choice with pros/cons, including estimated dependency count
- If custom: sketch of the adapter interface (what the adapter needs to do differently from oa-compat)
- Which specific models require the reasoning format (or how to detect it)
