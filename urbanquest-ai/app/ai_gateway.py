from __future__ import annotations

from collections import defaultdict
from datetime import date
from threading import Lock

from fastapi import APIRouter, HTTPException

from app.chat.models import ChatAction, ChatRequest, ChatResponse
from app.chat.service import ChatService
from app.config import get_settings

router = APIRouter(prefix="/api/ai", tags=["ai"])
settings = get_settings()
_usage: dict[tuple[str, date], int] = defaultdict(int)
_usage_lock = Lock()
_chat_service: ChatService | None = None


def configure(chat_service: ChatService) -> None:
    global _chat_service
    _chat_service = chat_service


def _bounded_history(request: ChatRequest) -> list:
    return request.history[-settings.max_history_messages :]


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest) -> ChatResponse:
    if _chat_service is None:
        raise HTTPException(status_code=503, detail="AI service is not ready.")
    chat_service = _chat_service
    user_key = request.user_id or "anonymous"
    usage_key = (user_key, date.today())
    with _usage_lock:
        if _usage[usage_key] >= settings.free_daily_ai_requests:
            raise HTTPException(status_code=429, detail="Daily AI request limit reached.")
        _usage[usage_key] += 1

    history = _bounded_history(request)
    if chat_service.estimate_tokens(request.message, history) > settings.max_input_tokens:
        raise HTTPException(status_code=413, detail="That request is too large. Shorten the message history.")
    response = await chat_service.respond(request.message, request.context, history)
    response.usage.total_tokens = response.usage.input_tokens + response.usage.output_tokens
    response.actions = [
        ChatAction(
            type="update_trip",
            payload={"trip_id": request.trip_id or "", "category": chat_service.extract_intent(request.message).category},
        )
    ]
    return response
