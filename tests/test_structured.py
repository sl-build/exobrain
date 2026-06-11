"""Tests for exocortex.structured module."""

import json

import pytest

from exocortex.structured import build_json_output, strip_code_fences, validate_json_output


class TestStripCodeFences:
    """Code fence stripping for --json mode."""

    def test_json_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert strip_code_fences(text) == '{"key": "value"}'

    def test_plain_fence(self):
        text = '```\nsome code\n```'
        assert strip_code_fences(text) == "some code"

    def test_no_fence(self):
        text = "plain text"
        assert strip_code_fences(text) == "plain text"


class TestBuildJsonOutput:
    """JSON output must be valid and contain response."""

    def test_basic_output(self):
        result = build_json_output("hello", model="gpt-test", prompt_tokens=None, completion_tokens=None, total_tokens=None, cost_usd=None, latency_ms=None)
        parsed = json.loads(result)
        assert parsed["response"] == "hello"
        assert "usage" not in parsed

    def test_with_stats(self):
        result = build_json_output("hello", model="gpt-test", prompt_tokens=10, completion_tokens=5, total_tokens=15, cost_usd=0.001, latency_ms=1200.0)
        parsed = json.loads(result)
        assert parsed["response"] == "hello"
        assert parsed["usage"]["model"] == "gpt-test"
        assert parsed["usage"]["prompt_tokens"] == 10
        assert parsed["usage"]["latency_ms"] == 1200.0


class TestValidateJsonOutput:
    def test_valid_json(self):
        text = '{"a": 1}'
        assert validate_json_output(text) == '{"a": 1}'

    def test_invalid_json(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            validate_json_output("not json at all")

    def test_json_in_fence(self):
        text = '```json\n{"a": 1}\n```'
        result = validate_json_output(text)
        assert json.loads(result) == {"a": 1}
