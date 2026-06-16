"""Tests for exobrain.config module."""

import pytest

from exobrain.config import load_config, save_config


class TestConfig:
    def test_default_config(self, mock_config_dir):
        config = load_config()
        assert config["provider"] == "openrouter"
        assert config["model"] == ""

    def test_save_and_load_provider(self, mock_config_dir):
        save_config("provider", "opencode_go")
        config = load_config()
        assert config["provider"] == "opencode_go"

    def test_save_and_load_model(self, mock_config_dir):
        save_config("model", "gpt-4o")
        config = load_config()
        assert config["model"] == "gpt-4o"

    def test_invalid_key_raises(self, mock_config_dir):
        with pytest.raises(ValueError, match="Invalid config key"):
            save_config("bad_key", "value")

    def test_save_preserves_custom_providers(self, mock_config_dir):
        """Regression: save_config() must not destroy [providers.*] sections.

        Bug: previously, save_config() wrote only [defaults] and dropped the
        provider_config dict, so any `exobrain config-set` after a custom
        provider was defined would silently remove the provider and break
        exobrain think for that provider.
        """
        from exobrain.config import save_provider_config

        # Seed a custom provider
        save_provider_config(
            name="opencode_go",
            provider_type="anthropic-compatible",
            base_url="https://opencode.ai/zen/go/v1",
            api_key_env="OPENCODE_GO_API_KEY",
            default_model="qwen3.7-max",
        )
        # Update an unrelated default — this used to wipe [providers.*]
        save_config("model", "qwen3.7-max")
        # Custom provider must survive
        config = load_config()
        assert "provider_config" in config, (
            "save_config() dropped [providers.*] sections — regression!"
        )
        assert "opencode_go" in config["provider_config"]
        prov = config["provider_config"]["opencode_go"]
        assert prov["type"] == "anthropic-compatible"
        assert prov["base_url"] == "https://opencode.ai/zen/go/v1"
        assert prov["api_key_env"] == "OPENCODE_GO_API_KEY"
        assert prov["default_model"] == "qwen3.7-max"
        # And the unrelated default was actually saved
        assert config["model"] == "qwen3.7-max"

    def test_save_round_trip_with_provider_list(self, mock_config_dir):
        """Regression: lists in [providers.*] survive save_config() round-trip."""
        from exobrain.config import save_provider_config

        save_provider_config(
            name="opencode_go",
            provider_type="anthropic-compatible",
            base_url="https://opencode.ai/zen/go/v1",
            api_key_env="OPENCODE_GO_API_KEY",
            default_model="qwen3.7-max",
        )
        # Manually inject a list field (save_provider_config doesn't take models list)
        import tomllib
        from pathlib import Path
        from exobrain.config import CONFIG_FILE

        # Re-read, add models list, re-write via save_config (no-op key update)
        save_config("timeout", 180)
        # Inject models list by parsing and rewriting
        text = CONFIG_FILE.read_text()
        # Append a list field manually (simulates user-defined list)
        text += '\nmodels = ["qwen3.7-max", "qwen3.6-plus"]\n'
        CONFIG_FILE.write_text(text)
        # Now trigger save_config again — list must survive
        save_config("timeout", 180)
        config = load_config()
        assert config["provider_config"]["opencode_go"]["models"] == [
            "qwen3.7-max",
            "qwen3.6-plus",
        ]
