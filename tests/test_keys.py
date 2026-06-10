"""Tests for brain.keys module."""

from brain.keys import (
    PROVIDERS,
    VALID_PROVIDERS,
    find_key_source,
    get_base_url,
    get_default_model,
    set_api_key,
)


class TestProviders:
    """Providers must match the article's description."""

    def test_openrouter_provider(self):
        assert "openrouter" in PROVIDERS
        assert PROVIDERS["openrouter"]["base_url"] == "https://openrouter.ai/api/v1"

    def test_opencode_go_provider(self):
        assert "opencode_go" in PROVIDERS
        assert PROVIDERS["opencode_go"]["base_url"] == "https://opencode.ai/zen/go/v1"

    def test_valid_providers_list(self):
        assert set(VALID_PROVIDERS) == {"openrouter", "opencode_go"}


class TestKeyManagement:
    def test_set_and_find_key(self, mock_env_files, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("BRAIN_API_KEY", raising=False)
        path = set_api_key("sk-test-12345")
        assert path.exists()

    def test_find_key_from_env(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-env-key")
        result = find_key_source()
        assert result is not None
        key, path = result
        assert key == "sk-env-key"

    def test_env_var_override(self, monkeypatch):
        """Provider-specific env var takes precedence."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-override")
        monkeypatch.setenv("BRAIN_API_KEY", "sk-generic")
        from brain.keys import get_api_key

        key = get_api_key("openrouter")
        assert key == "sk-override"


class TestBaseUrls:
    def test_openrouter_url(self):
        assert get_base_url("openrouter") == "https://openrouter.ai/api/v1"

    def test_opencode_go_url(self):
        assert get_base_url("opencode_go") == "https://opencode.ai/zen/go/v1"

    def test_env_override_url(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_BASE_URL", "https://custom.api/v1")
        assert get_base_url("openrouter") == "https://custom.api/v1"


class TestDefaultModels:
    def test_openrouter_default(self):
        assert get_default_model("openrouter") == "openai/gpt-5.5"

    def test_opencode_go_default(self):
        assert get_default_model("opencode_go") == "qwen3.7-max"
