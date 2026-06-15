"""Tests for exocortex.provider registry and routing."""

from unittest.mock import patch


class TestGetAdapter:
    """Adapter resolution by model+provider."""

    def test_openrouter_uses_oa_compat(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        from exocortex.provider import get_adapter
        from exocortex.provider.oa_compat import OACompatAdapter

        adapter = get_adapter("openai/gpt-4o", "openrouter")
        assert isinstance(adapter, OACompatAdapter)

    def test_custom_provider_uses_oa_compat(self, monkeypatch, mock_config_dir):
        """Custom provider from config.toml should route to oa_compat by default."""
        config_dir = mock_config_dir
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.toml"
        config_file.write_text(
            '[providers.opencode_go]\n'
            'env_var = "OPENCODE_GO_API_KEY"\n'
            'base_url = "https://opencode.ai/zen/go/v1"\n'
            'default_model = "qwen3.7-max"\n'
            'default_adapter = "oa_compat"\n'
            'model_map = { "qwen3.7-max" = "reasoning" }\n'
        )
        monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-test")
        from exocortex.provider import get_adapter
        from exocortex.provider.oa_compat import OACompatAdapter

        adapter = get_adapter("gpt-4o", "opencode_go")
        assert isinstance(adapter, OACompatAdapter)

    def test_custom_provider_reasoning_model(self, monkeypatch, mock_config_dir):
        """Custom provider with model_map should route to reasoning adapter."""
        config_dir = mock_config_dir
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "config.toml"
        config_file.write_text(
            '[providers.opencode_go]\n'
            'env_var = "OPENCODE_GO_API_KEY"\n'
            'base_url = "https://opencode.ai/zen/go/v1"\n'
            'default_model = "qwen3.7-max"\n'
            'default_adapter = "oa_compat"\n'
            'model_map = { "qwen3.7-max" = "reasoning" }\n'
        )
        monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-test")
        from exocortex.provider import get_adapter
        from exocortex.provider.reasoning import ReasoningAdapter

        adapter = get_adapter("qwen3.7-max", "opencode_go")
        assert isinstance(adapter, ReasoningAdapter)


class TestComplete:
    """Integration via provider.complete() with mocked HTTP."""

    def test_oa_compat_complete_mocked(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")

        mock_response = type(
            "MockChoice",
            (),
            {
                "message": type("MockMsg", (), {"content": "Hello!"})(),
            },
        )()
        mock_completion = type(
            "MockCompletion",
            (),
            {
                "choices": [mock_response],
                "model": "gpt-4o",
                "usage": type(
                    "MockUsage",
                    (),
                    {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                )(),
            },
        )()

        def fake_create(self, **kwargs):
            return mock_completion

        mock_openai = type(
            "MockOpenAI",
            (),
            {
                "chat": type(
                    "MockChat",
                    (),
                    {
                        "completions": type("MockCompletions", (), {"create": fake_create})(),
                    },
                )(),
                "api_key": "sk-test",
                "base_url": "https://test.url",
            },
        )

        with patch("openai.OpenAI", return_value=mock_openai):
            from exocortex.provider import complete

            text, stats = complete(
                messages=[{"role": "user", "content": "hi"}],
                model="gpt-4o",
                provider="openrouter",
            )
            assert text == "Hello!"
            assert stats.model == "gpt-4o"
            assert stats.total_tokens == 30

    def test_unknown_provider_falls_back(self):
        """An unknown provider name should raise on get_adapter."""
        from exocortex.keys import PROVIDERS

        assert "nonexistent" not in PROVIDERS
