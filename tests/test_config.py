"""Tests for exocortex.config module."""

import pytest

from exocortex.config import load_config, save_config


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
