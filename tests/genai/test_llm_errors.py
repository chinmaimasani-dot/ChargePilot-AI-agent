"""LLM error normalization tests."""

from app.llm.errors import (
    GenAIError,
    GenAIUnavailableError,
    normalize_provider_error,
)


def test_provider_error_is_normalized_to_safe_error():
    normalized = normalize_provider_error(
        RuntimeError("https://openrouter.ai failed with key sk-secret-123")
    )
    assert isinstance(normalized, GenAIUnavailableError)
    # The raw provider message (URLs, keys) must not leak through.
    assert "sk-secret" not in normalized.message
    assert "openrouter" not in normalized.message


def test_genai_errors_pass_through():
    original = GenAIError("safe message")
    assert normalize_provider_error(original) is original


def test_error_codes_are_stable():
    assert GenAIUnavailableError().code == "genai_unavailable"
    assert GenAIError().code == "genai_error"
