"""Tests for exobrain.errors module."""

from exobrain.errors import (
    API_FAILURE,
    BAD_RESPONSE,
    INPUT_ERROR,
    SUCCESS,
    APIError,
    BadResponseError,
    BrainError,
    InputError,
    RetryableError,
)


class TestExitCodes:
    """Article: clean exit codes for agent pipelines."""

    def test_success(self):
        assert SUCCESS == 0

    def test_api_failure(self):
        assert API_FAILURE == 1

    def test_bad_response(self):
        assert BAD_RESPONSE == 2

    def test_input_error(self):
        assert INPUT_ERROR == 3


class TestExceptionHierarchy:
    """All custom exceptions inherit from BrainError."""

    def test_api_error_is_brain_error(self):
        assert issubclass(APIError, BrainError)

    def test_bad_response_is_brain_error(self):
        assert issubclass(BadResponseError, BrainError)

    def test_input_error_is_brain_error(self):
        assert issubclass(InputError, BrainError)

    def test_retryable_is_brain_error(self):
        assert issubclass(RetryableError, BrainError)

    def test_api_error_status_code(self):
        e = APIError("fail", status_code=429)
        assert e.status_code == 429

    def test_retryable_status_code(self):
        e = RetryableError("retry", status_code=500)
        assert e.status_code == 500
