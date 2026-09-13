import re
import json
from datetime import date
from openai import AsyncOpenAI

from app.ai_prompt import URBANQUEST_SYSTEM_PROMPT
from app.chat.models import ChatResponse, ExtractedTripState, TokenUsage
from app.config import get_settings
from app.planner.models import PlannerIntent, TravelerContext
from app.planner.service import AdventurePlanner


class ChatService:
    def __init__(self, planner: AdventurePlanner) -> None:
        self.planner = planner
        settings = get_settings()
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_model

    async def respond(self, message: str, context: TravelerContext, history: list[object] | None = None) -> ChatResponse:
        extracted = await self.extract_trip_state(message, context, history or [])
        intent = self.extract_intent(message, extracted)
        context = self.apply_trip_state(context, extracted)
        plan = await self.planner.create_plan(context=context, intent=intent)
        input_tokens = self.estimate_tokens(message, history or [])
        output_tokens = min(get_settings().max_output_tokens, self.estimate_tokens(plan.title, []))
        return ChatResponse(
            message=(
                self.response_message(extracted, context, intent)
            ),
            plan=plan,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
            ),
        )

    @staticmethod
    def estimate_tokens(text: str, history: list[object]) -> int:
        history_text = " ".join(
            getattr(item, "content", "") for item in history
        )
        return max(1, (len(f"{text} {history_text}") + 3) // 4)

    async def extract_trip_state(self, message: str, context: TravelerContext, history: list[object]) -> ExtractedTripState:
        if not self.openai:
            return ExtractedTripState()
        payload = {
            "TripState": context.model_dump(),
            "latest_message": message,
            "recent_messages": [getattr(item, "model_dump", lambda: {})() for item in history[-12:]],
        }
        response = await self.openai.chat.completions.create(
            model=self.model,
            temperature=0,
            max_tokens=get_settings().max_output_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": URBANQUEST_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return ExtractedTripState.model_validate_json(content)

    @staticmethod
    def apply_trip_state(context: TravelerContext, extracted: ExtractedTripState) -> TravelerContext:
        updated = context.model_copy(deep=True)
        if extracted.destination:
            updated.destination.city = extracted.destination.split(",")[0].strip()
        if extracted.origin:
            updated.home.city = extracted.origin.split(",")[0].strip()
        if extracted.departure_date:
            updated.departure_date = extracted.departure_date
        if extracted.return_date:
            updated.return_date = extracted.return_date
        if extracted.travelers:
            updated.travelers = extracted.travelers
        if extracted.budget is not None:
            updated.budget_home = extracted.budget
        if extracted.preferences:
            updated.interests = extracted.preferences
        if updated.departure_date and updated.return_date:
            start = date.fromisoformat(updated.departure_date)
            end = date.fromisoformat(updated.return_date)
            updated.available_minutes = max(1, (end - start).days + 1) * 1440
        return updated

    @staticmethod
    def response_message(extracted: ExtractedTripState, context: TravelerContext, intent: PlannerIntent) -> str:
        services = extracted.requested_services
        if services:
            return f"Got it. You're traveling from {context.home.city} to {context.destination.city}. I'll work on {', '.join(services)}."
        return f"I'll shape a {intent.category} plan for {context.destination.city} around your time and budget."

    @staticmethod
    def extract_intent(message: str, extracted: ExtractedTripState | None = None) -> PlannerIntent:
        normalized = message.lower()
        categories = {
            "history": ("historic", "historical", "history", "heritage"),
            "food": ("food", "cafe", "café", "eat", "local cuisine"),
            "nature": ("nature", "park", "outdoor", "hike", "green"),
            "art": ("art", "gallery", "museum", "creative"),
        }
        category = next(
            (
                name
                for name, keywords in categories.items()
                if any(keyword in normalized for keyword in keywords)
            ),
            "culture",
        )

        duration_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(day|days|hour|hours|hr|hrs)", normalized
        )
        duration_minutes = None
        if duration_match:
            value = float(duration_match.group(1))
            duration_minutes = int(
                value * (1440 if "day" in duration_match.group(2) else 60)
            )

        if extracted and "nature" in extracted.preferences:
            category = "nature"
        return PlannerIntent(
            category=category,
            duration_minutes=duration_minutes,
            avoid_expensive="cheap" in normalized
            or "budget" in normalized
            or "affordable" in normalized,
            adventurous="adventurous" in normalized
            or "offbeat" in normalized
            or "hidden" in normalized,
        )
