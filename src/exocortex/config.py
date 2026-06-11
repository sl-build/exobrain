"""Exocortex CLI — Persistent config file support."""

from __future__ import annotations

from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "exocortex"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _ensure_config() -> None:
    """Ensure config directory and file exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text('[defaults]\nprovider = "openrouter"\nmodel = ""\n')


def load_config() -> dict:
    """Read config file, return dict with all sections."""
    import tomllib

    _ensure_config()
    data = CONFIG_FILE.read_text()
    parsed = tomllib.loads(data)
    defaults = parsed.get("defaults", {})

    result: dict = {
        "provider": defaults.get("provider", "openrouter"),
        "model": defaults.get("model", ""),
    }

    # Provider-specific config
    provider_configs = {}
    for key, val in parsed.items():
        if key.startswith("provider."):
            provider_name = key.split(".", 1)[1]
            if isinstance(val, dict):
                provider_configs[provider_name] = val

    if provider_configs:
        result["provider_config"] = provider_configs

    return result


def save_config(key: str, value: str) -> None:
    """Update a config key and save the file."""
    if key not in ("provider", "model"):
        raise ValueError(f"Invalid config key: {key}")
    _ensure_config()
    config = load_config()
    config[key] = value

    lines = ["[defaults]"]
    for k, v in config.items():
        if k == "provider_config":
            continue
        if v == "":
            lines.append(f'{k} = ""')
        else:
            lines.append(f'{k} = "{v}"')
    CONFIG_FILE.write_text("\n".join(lines) + "\n")


def get_default_provider() -> str:
    """Return the default provider from config."""
    return load_config()["provider"]


def get_default_model() -> str | None:
    """Return the default model from config, or None if empty."""
    model = load_config()["model"]
    return model if model else None


def get_provider_model_map(provider: str) -> dict[str, str]:
    """Return model_map for a provider from config.toml."""
    config = load_config()
    provider_configs = config.get("provider_config", {})
    prov = provider_configs.get(provider, {})
    return prov.get("model_map", {})
