# Troubleshooting

## Deep reasoning hangs (`--depth deep` or `--depth exhaustive`)

**Symptom:** `exobrain think "..." --depth deep` hangs indefinitely or times out.

**Cause:** The GLM-5.2 reasoning model generates extensive internal `reasoning_content` (chain-of-thought) before producing visible output. With `--depth deep` (`max_tokens=16384`), complex prompts can produce 2000–3000+ completion tokens, taking 80–200s server-side.

**Fix:** Default timeout is now 350s (as of v0.2.6). If still not enough:

```bash
exobrain config-set timeout 600
```

**Observed latency by depth (GLM-5.2, complex prompt):**

| Depth | max_tokens | Typical latency |
|-------|-----------|-----------------|
| quick | 4096 | ~2s |
| normal | 8192 | ~40–50s |
| deep | 16384 | ~80–90s |
| exhaustive | 32768 | >200s |

**Notes:**
- The model returns `reasoning_content` (hidden) + `content` (visible). Both count toward `max_tokens`.
- The OpenAI SDK sends `x-stainless-read-timeout` header to the server. If the server doesn't honor it, the client-side httpx timeout is the only safeguard.
- `--depth quick` is fine for simple questions. Use `--depth deep` only when you need thorough analysis.

## No output / empty response

**Cause:** Model returned empty `content` field (possible with reasoning models that put everything in `reasoning_content`).

**Fix:** The adapter raises `BadResponseError("Empty response from model")` and retries. If persistent, try `--depth normal` instead of `--depth deep`.

## Provider returns 401 / "missing authorization header"

**Cause:** API key not found or wrong env var name.

**Fix:**
```bash
exobrain key          # check current key
exobrain key-set KEY  # set new key
```

Key lookup order:
1. Provider-specific env var (e.g. `GOMODEL_API_KEY`)
2. `EXOBRAIN_API_KEY`
3. Profile `.env` (`~/.hermes/profiles/goose/.env`)
4. Global `.env` (`~/.hermes/.env`)
5. OpenRouter fallback

## Provider returns "model not supported"

**Cause:** Model name doesn't match what the provider expects.

**Fix:** Check valid models:
```bash
exobrain providers    # list providers and default models
curl http://localhost:8080/v1/models  # list available models (with auth)
```
