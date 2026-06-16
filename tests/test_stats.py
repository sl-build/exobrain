"""Tests for exobrain.stats module."""

from exobrain.stats import COST_PER_1M_TOKENS, Stats


class TestStats:
    def test_calculate_cost_known_model(self):
        s = Stats(model="openai/gpt-5.5")
        s.prompt_tokens = 1000000
        s.completion_tokens = 1000000
        cost = s.calculate_cost()
        assert cost is not None
        assert cost == COST_PER_1M_TOKENS["openai/gpt-5.5"]["input"] + COST_PER_1M_TOKENS["openai/gpt-5.5"]["output"]

    def test_calculate_cost_unknown_model(self):
        s = Stats(model="unknown/model")
        assert s.calculate_cost() is None

    def test_report_format(self):
        s = Stats(model="test-model", latency_ms=1500.0)
        s.prompt_tokens = 100
        s.completion_tokens = 50
        s.total_tokens = 150
        report = s.report(to_stderr=False)
        assert "test-model" in report
        assert "100" in report
        assert "1.5s" in report

    def test_empty_stats(self):
        s = Stats()
        report = s.report(to_stderr=False)
        assert "unknown" in report
