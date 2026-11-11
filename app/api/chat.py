"""Chat orchestration endpoint (Member 4).

Contract agreed with Member 1:

- Request: conversation identifier (optional; created when absent), user
  message, optional confirmation action tied to a pending proposal id.
- Role context is derived from the authenticated identity. TEMPORARY dev
  mode: until Member 1's JWT dependency lands, identity is taken from the
  `X-User-Id` / `X-User-Role` headers and MUST be replaced by
  `get_current_user` before production use.
- Response: structured payload (reply, sources, tool results, pending
  confirmation metadata).
"""

import logging
import uuid
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.shared.runtime import ChatRuntime, get_runtime
from app.llm.errors import GenAIError
from app.mcp.client.manager import build_user_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatMessageRequest(BaseModel):
    conversation_id: str | None = Field(
        default=None, description="Existing conversation; omit to start a new one."
    )
    message: str = Field(min_length=1, max_length=4000)
    action: Literal["send", "confirm", "reject"] = "send"
    proposal_id: str | None = Field(
        default=None,
        description="Required with action=confirm/reject: the pending proposal to resolve.",
    )


class ChatMessageResponse(BaseModel):
    conversation_id: str
    reply: str
    route: str | None = None
    sources: list[dict] = []
    tool_results: list[dict] = []
    pending_confirmation: dict | None = None


@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    # TODO(Member 1 integration): replace this dev shim with the shared
    # `get_current_user` JWT dependency; keep the same user_context dict.
    x_user_id: str = Header(..., description="Dev-mode user id from verified identity"),
    x_user_role: Literal["owner", "driver"] = Header(
        ..., description="Dev-mode role from verified identity"
    ),
) -> ChatMessageResponse:
    conversation_id = payload.conversation_id or str(uuid.uuid4())
    user_context = build_user_context(x_user_id, x_user_role)
    runtime: ChatRuntime = get_runtime()

    try:
        if payload.action in {"confirm", "reject"}:
            if not payload.proposal_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="proposal_id is required for confirm/reject actions.",
                )
            if payload.action == "confirm":
                result = await runtime.confirm_pending(
                    user_context, conversation_id, payload.proposal_id
                )
            else:
                result = await runtime.reject_pending(
                    user_context, conversation_id, payload.proposal_id
                )
        else:
            result = await runtime.run_turn(user_context, conversation_id, payload.message)
    except GenAIError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message
        ) from exc

    return ChatMessageResponse(**result)


@router.get("/health")
async def genai_health() -> dict:
    """Liveness of the GenAI layer and MCP server registration status."""
    runtime = get_runtime()
    return {"status": "ok", "mcp_servers": runtime.mcp_manager.server_status()}
