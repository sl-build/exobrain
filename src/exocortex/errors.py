"""Exocortex CLI — Exit codes and custom exceptions."""

# Exit codes
SUCCESS = 0
API_FAILURE = 1
BAD_RESPONSE = 2
INPUT_ERROR = 3


class BrainError(Exception):
    """Base exception for Exocortex CLI."""


class APIError(BrainError):
    """API/network failure after retries exhausted."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BadResponseError(BrainError):
    """Invalid or empty model response."""


class InputError(BrainError):
    """Bad input: missing key, file not found, invalid args."""


class RetryableError(BrainError):
    """Transient error that can be retried (429, 5xx)."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code