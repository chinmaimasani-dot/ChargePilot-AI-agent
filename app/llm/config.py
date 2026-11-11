"""Configuration for the shared GenAI layer (Member 4).

Environment-based settings. Secrets are read from the environment only and
must never be committed to source control.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class GenAISettings(BaseSettings):
    """Settings for OpenRouter access and shared graph behaviour."""

    model_config = SettingsConfigDict(
        env_prefix="",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- OpenRouter / LLM provider ---
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 60.0
    llm_max_retries: int = 2

    # --- Shared graph behaviour ---
    # Hard cap on tool-call rounds inside one user turn so a misbehaving
    # model can never loop indefinitely.
    max_tool_call_rounds: int = 5

    # --- MCP servers (registered when Members 2/3 deliver them) ---
    # Empty means "server not available yet"; the graph falls back to
    # general/RAG routing for that role.
    mcp_owner_server_url: str = ""
    mcp_driver_server_url: str = ""


@lru_cache
def get_genai_settings() -> GenAISettings:
    return GenAISettings()
