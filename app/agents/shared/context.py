"""Conversation context loading/saving (Member 4, in coordination with Member 1).

Member 1 owns the conversations/messages tables and persistence services.
Until that lands, this module provides the interface the graph runtime uses
plus an in-memory development implementation. When Member 1's persistence is
available, only `create_conversation_store` changes — graph code does not.
"""

from typing import Any, Protocol


class ConversationStore(Protocol):
    """Persistence contract required by the chat runtime."""

    def load_history(
        self, conversation_id: str, user_id: str
    ) -> list[dict[str, str]]:
        """Return prior messages [{"role": "user"|"assistant", "content": ...}]."""
        ...

    def append_message(
        self, conversation_id: str, user_id: str, role: str, content: str
    ) -> None:
        ...

    def set_pending_confirmation(
        self, conversation_id: str, user_id: str, proposal: dict | None
    ) -> None:
        """Store or clear the pending action awaiting explicit user approval."""
        ...

    def get_pending_confirmation(
        self, conversation_id: str, user_id: str
    ) -> dict | None:
        ...


class InMemoryConversationStore:
    """Dev-only store. NOT for production: swap for Member 1's persistence."""

    def __init__(self) -> None:
        self._messages: dict[tuple[str, str], list[dict[str, str]]] = {}
        self._pending: dict[tuple[str, str], dict | None] = {}

    def load_history(
        self, conversation_id: str, user_id: str
    ) -> list[dict[str, str]]:
        return list(self._messages.get((conversation_id, user_id), []))

    def append_message(
        self, conversation_id: str, user_id: str, role: str, content: str
    ) -> None:
        self._messages.setdefault((conversation_id, user_id), []).append(
            {"role": role, "content": content}
        )

    def set_pending_confirmation(
        self, conversation_id: str, user_id: str, proposal: dict | None
    ) -> None:
        key = (conversation_id, user_id)
        if proposal is None:
            self._pending.pop(key, None)
        else:
            self._pending[key] = proposal

    def get_pending_confirmation(
        self, conversation_id: str, user_id: str
    ) -> dict | None:
        return self._pending.get((conversation_id, user_id))


_store: ConversationStore = InMemoryConversationStore()


def get_conversation_store() -> ConversationStore:
    """Single access point for the runtime; swap point for Member 1."""
    return _store


def set_conversation_store(store: ConversationStore) -> None:
    """Replace the process-wide store (used by tests and by integration)."""
    global _store
    _store = store
