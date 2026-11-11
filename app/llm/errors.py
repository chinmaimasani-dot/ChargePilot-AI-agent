"""Controlled error types for the GenAI layer.

Provider/API failures must surface as backend-controlled errors and must
never leak API keys, base URLs with credentials, or internal stack traces to
clients or into LLM-visible tool results.
"""


class GenAIError(Exception):
    """Base class for controlled GenAI-layer failures."""

    code = "genai_error"
    message = "The AI assistant could not complete this request."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail
        super().__init__(self.message)


class GenAIUnavailableError(GenAIError):
    """The LLM/embedding provider is unreachable, misconfigured or failing."""

    code = "genai_unavailable"
    message = "The AI service is temporarily unavailable. Please try again later."


class GenAIRoutingError(GenAIError):
    """The request could not be routed to a valid workflow."""

    code = "genai_routing_error"
    message = "The request could not be processed for your role."


class ToolExecutionError(GenAIError):
    """A tool call failed; details are safe to expose to the graph."""

    code = "tool_execution_error"
    message = "The requested operation could not be completed."


def normalize_provider_error(exc: Exception) -> GenAIError:
    """Convert any provider/SDK exception into a safe backend error.

    Never include raw exception text in the returned error: provider SDK
    messages can embed endpoint URLs or authorization material.
    """
    if isinstance(exc, GenAIError):
        return exc
    return GenAIUnavailableError()
