"""Shared fakes and fixtures for GenAI-layer tests (Member 4).

All tests run offline: the chat model and tool executors are fakes, the
conversation store is in-memory, and no database is required.
"""

from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.agents.shared.context import InMemoryConversationStore, set_conversation_store
from app.llm.client import set_chat_model_override
from app.mcp.client.manager import MCPClientManager


class FakeChatModel(BaseChatModel):
    """Scripted chat model.

    `responder` receives the list of messages and returns the message to
    produce. Used to fake routing answers, tool-call proposals and replies.
    """

    responder: Any = None
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake"

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):  # noqa: ANN001
        self.calls += 1
        message = self.responder(messages)
        if isinstance(message, str):
            message = AIMessage(content=message)
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):  # noqa: ANN001
        return self._generate(messages, stop, run_manager, **kwargs)


def make_fake_model(responder):
    return FakeChatModel(responder=responder)


@pytest.fixture()
def fresh_manager():
    return MCPClientManager()


@pytest.fixture()
def offline_genai(monkeypatch):
    """Reset model override and conversation store around each test."""
    store = InMemoryConversationStore()
    set_conversation_store(store)
    yield store
    set_chat_model_override(None)
    set_conversation_store(InMemoryConversationStore())
