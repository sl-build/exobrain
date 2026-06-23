# Changelog

## v0.2.6 — 2026-06-23

### Fixed

- **Default timeout 180s → 350s.** Deep reasoning (`--depth deep`) with complex prompts generates 2000–3000+ tokens and can take 80–200s. The previous 180s default was insufficient, causing hangs and forced kills. Bumped across all fallbacks: `config.py`, `client.py`, `oa_compat.py`, `reasoning.py`.

### Root Cause

`--depth deep` sets `max_tokens=16384`. With the GLM-5.2 reasoning model, complex prompts trigger extensive `reasoning_content` generation before the final answer. Observed latencies:

| Depth | max_tokens | Latency (complex prompt) |
|-------|-----------|--------------------------|
| quick | 4096 | ~2s |
| normal | 8192 | ~43s |
| deep | 16384 | ~81–86s |
| exhaustive | 32768 | >200s (hangs at 180s) |

The model's `reasoning_content` field holds internal chain-of-thought that is not streamed to the user. With `max_tokens=16384`, the server generates thousands of reasoning tokens before producing the visible answer — easily exceeding a 180s timeout on complex prompts.

### Files Changed

```
src/exobrain/config.py            — template + load_config fallback
src/exobrain/client.py            — float conversion fallback
src/exobrain/provider/oa_compat.py  — OpenAI SDK adapter
src/exobrain/provider/reasoning.py  — Anthropic SDK adapter
```
