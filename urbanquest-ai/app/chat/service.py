import re

from app.chat.models import ChatResponse
from app.planner.models import PlannerIntent, TravelerContext
from app.planner.service import AdventurePlanner


class ChatService:
    def __init__(self, planner: AdventurePlanner) -> None:
        self.planner = planner

    async def respond(self, message: str, context: TravelerContext) -> ChatResponse:
        intent = self.extract_intent(message)
        plan = await self.planner.create_plan(context=context, intent=intent)
        return ChatResponse(
            message=(
                f"I found a {intent.category} adventure in "
                f"{context.destination.city} that fits your time and budget."
            ),
            plan=plan,
        )

    @staticmethod
    def extract_intent(message: str) -> PlannerIntent:
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

        duration_match = re.search(r"(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs)", normalized)
        duration_minutes = (
            int(float(duration_match.group(1)) * 60)
            if duration_match
            else None
        )

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
