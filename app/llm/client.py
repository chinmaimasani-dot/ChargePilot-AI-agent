"""Reusable OpenRouter chat-model client (Member 4).

Members 2 and 3 must use this module instead of creating their own LLM
clients. Model selection, timeout, retry policy and error handling are
centralized here.
"""

import logging
from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.llm.config import GenAISettings, get_genai_settings
from app.llm.errors import normalize_provider_error

logger = logging.getLogger(__name__)


def _build_chat_model(settings: GenAISettings) -> BaseChatModel:
    """Instantiate the OpenRouter-backed chat model.

    OpenRouter speaks the OpenAI wire protocol, so ChatOpenAI with a custom
    base_url is the supported integration path.
    """
    if not settings.openrouter_api_key:
        # Fail fast at call time rather than import time so the app can
        # still boot (and tests can run offline with fake models).
        raise normalize_provider_error(RuntimeError("missing openrouter api key"))

    try:
        return ChatOpenAI(
            model=settings.openrouter_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    except Exception as exc:  # pragma: no cover - constructor is defensive
        raise normalize_provider_error(exc) from exc


@lru_cache
def get_chat_model() -> BaseChatModel:
    """Return the process-wide configured chat model.

    Tests inject fakes via `set_chat_model_override` / reset cache instead of
    hitting the provider.
    """
    return _build_chat_model(get_genai_settings())


_model_override: BaseChatModel | None = None


def set_chat_model_override(model: BaseChatModel | None) -> None:
    """Test helper: force `get_chat_model` to return a specific (fake) model."""
    global _model_override
    _model_override = model


def get_chat_model_for_role(role: str) -> BaseChatModel:
    """Resolve the chat model for a trusted role context.

    Kept as a seam so role-specific model selection can be added later
    without touching graph code.
    """
    if _model_override is not None:
        return _model_override
    return get_chat_model()
