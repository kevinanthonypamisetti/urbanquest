from __future__ import annotations

from collections import defaultdict
from datetime import date
from threading import Lock

import asyncio
import json
from urllib.request import Request as UrlRequest, urlopen

from fastapi import APIRouter, HTTPException, Request

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


async def _authenticated_user(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication expired. Sign in again.")
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise HTTPException(status_code=503, detail="Authentication service is not configured.")

    token = authorization.removeprefix("Bearer ").strip()

    def lookup() -> dict:
        endpoint = f"{settings.supabase_url.rstrip('/')}/auth/v1/user"
        probe = UrlRequest(
            endpoint,
            headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {token}"},
        )
        with urlopen(probe, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        user = await asyncio.to_thread(lookup)
    except Exception as error:
        raise HTTPException(status_code=401, detail="Authentication expired. Sign in again.") from error
    if not user.get("id"):
        raise HTTPException(status_code=401, detail="Authentication expired. Sign in again.")
    return str(user["id"])


def _default_context() -> object:
    from app.planner.models import Location, TravelerContext

    return TravelerContext(
        home=Location(country="Unknown", city="Unknown"),
        destination=Location(country="Unknown", city="Unknown"),
        home_currency="USD",
        destination_currency="USD",
        budget_home=0,
        budget_destination=0,
        available_minutes=1440,
    )


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: Request, payload: ChatRequest) -> ChatResponse:
    if _chat_service is None:
        raise HTTPException(status_code=503, detail="AI service is not ready.")
    chat_service = _chat_service
    user_key = await _authenticated_user(request)
    usage_key = (user_key, date.today())
    with _usage_lock:
        if _usage[usage_key] >= settings.free_daily_ai_requests:
            raise HTTPException(status_code=429, detail="Daily AI request limit reached.")
        _usage[usage_key] += 1

    history = payload.history[-settings.max_history_messages :]
    if chat_service.estimate_tokens(payload.message, history) > settings.max_input_tokens:
        raise HTTPException(status_code=413, detail="That request is too large. Shorten the message history.")
    response = await chat_service.respond(payload.message, payload.context or _default_context(), history)
    response.usage.total_tokens = response.usage.input_tokens + response.usage.output_tokens
    response.actions = [
        ChatAction(
            type="update_trip",
            payload={"trip_id": payload.trip_id or "", "category": chat_service.extract_intent(payload.message).category},
        )
    ]
    return response
