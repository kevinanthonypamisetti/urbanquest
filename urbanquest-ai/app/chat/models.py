from pydantic import BaseModel, Field

from app.planner.models import AdventurePlan, TravelerContext


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    context: TravelerContext


class ChatResponse(BaseModel):
    message: str
    plan: AdventurePlan
