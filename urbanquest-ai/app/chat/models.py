from typing import Literal

from pydantic import BaseModel, Field

from app.planner.models import AdventurePlan, TravelerContext


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: TravelerContext
    trip_id: str | None = Field(default=None, max_length=100)
    user_id: str | None = Field(default=None, max_length=100)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatAction(BaseModel):
    type: Literal["add_activity", "remove_activity", "replace_day", "update_trip"]
    payload: dict[str, str | int | float | bool]


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    message: str
    plan: AdventurePlan
    actions: list[ChatAction] = Field(default_factory=list)
    usage: TokenUsage
