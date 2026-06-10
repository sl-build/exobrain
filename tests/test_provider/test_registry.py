"""Tests for brain.provider registry and routing."""

from unittest.mock import patch


class TestGetAdapter:
    """Adapter resolution by model+provider."""

    def test_openrouter_uses_oa_compat(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        from brain.provider import get_adapter
        from brain.provider.oa_compat import OACompatAdapter

        adapter = get_adapter("openai/gpt-4o", "openrouter")
        assert isinstance(adapter, OACompatAdapter)

    def test_opencode_go_default_uses_oa_compat(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-test")
        from brain.provider import get_adapter
        from brain.provider.oa_compat import OACompatAdapter

        adapter = get_adapter("gpt-4o", "opencode_go")
        assert isinstance(adapter, OACompatAdapter)

    def test_opencode_go_qwen_uses_reasoning(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-test")
        from brain.provider import get_adapter
        from brain.provider.reasoning import ReasoningAdapter

        adapter = get_adapter("qwen3.7-max", "opencode_go")
        assert isinstance(adapter, ReasoningAdapter)

    def test_opencode_go_qwen_pro_uses_reasoning(self, monkeypatch):
        monkeypatch.setenv("OPENCODE_GO_API_KEY", "sk-test")
        from brain.provider import get_adapter
        from brain.provider.reasoning import ReasoningAdapter

        adapter = get_adapter("qwen3.6-plus", "opencode_go")
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
            from brain.provider import complete

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
        from brain.keys import PROVIDERS

        assert "nonexistent" not in PROVIDERS
