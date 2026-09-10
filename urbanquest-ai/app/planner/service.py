from app.maps.provider import MapsProvider
from app.experience.engine import build_experience_bundle, build_trip_dna
from app.planner.models import (
    AdventurePlan,
    AdventureStop,
    BudgetBreakdown,
    PlannerIntent,
    TravelerContext,
)
from app.planner.scoring import score_place


class AdventurePlanner:
    def __init__(self, maps_provider: MapsProvider, max_candidates: int = 8) -> None:
        self.maps = maps_provider
        self.max_candidates = max_candidates

    async def create_plan(
        self, context: TravelerContext, intent: PlannerIntent
    ) -> AdventurePlan:
        places = await self.maps.nearby_places(
            latitude=context.destination.latitude,
            longitude=context.destination.longitude,
            radius=5000,
            category=intent.category,
            city=context.destination.city,
        )
        ranked = sorted(
            places,
            key=lambda place: score_place(place, context, intent),
            reverse=True,
        )[: self.max_candidates]

        requested_minutes = min(
            context.available_minutes,
            intent.duration_minutes or context.available_minutes,
        )
        days_count = max(1, (requested_minutes + 1439) // 1440)
        max_minutes = min(requested_minutes, 1440)
        stops: list[AdventureStop] = []
        elapsed = 0
        for place in ranked:
            if elapsed + place.duration_minutes > max_minutes:
                continue
            if (
                sum(stop.estimated_cost for stop in stops) + place.estimated_cost
                > context.budget_destination
            ):
                continue
            stops.append(
                AdventureStop(
                    name=place.name,
                    description=place.description,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    duration_minutes=place.duration_minutes,
                    estimated_cost=place.estimated_cost,
                )
            )
            elapsed += place.duration_minutes

        if not stops and ranked:
            place = ranked[0]
            stops.append(
                AdventureStop(
                    name=place.name,
                    description=place.description,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    duration_minutes=min(place.duration_minutes, max_minutes),
                    estimated_cost=min(
                        place.estimated_cost, context.budget_destination
                    ),
                )
            )

        estimated_cost = sum(stop.estimated_cost for stop in stops)
        duration = sum(stop.duration_minutes for stop in stops)
        distance = sum(
            place.distance_km
            for place in ranked
            if any(stop.name == place.name for stop in stops)
        )
        days = [
            {
                "day": day,
                "title": (
                    "Arrival and first impressions"
                    if day == 1
                    else "Local discoveries and slow travel"
                ),
                "activities": stops if day == 1 else [],
            }
            for day in range(1, days_count + 1)
        ]
        return AdventurePlan(
            title=f"{context.destination.city}: {intent.category.title()} field notes",
            description=(
                f"A considered {intent.category} route with {len(stops)} stops "
                f"and room for an unhurried pause."
            ),
            duration_minutes=duration,
            distance_km=round(distance, 1),
            estimated_cost=round(estimated_cost, 2),
            currency=context.destination_currency,
            stops=stops,
            days=days,
            budget=[
                BudgetBreakdown(
                    category="Experiences",
                    amount=round(estimated_cost, 2),
                    currency=context.destination_currency,
                ),
                BudgetBreakdown(
                    category="Remaining",
                    amount=round(
                        max(context.budget_destination - estimated_cost, 0), 2
                    ),
                    currency=context.destination_currency,
                ),
            ],
            reasoning=(
                "Places were filtered to the available time and destination budget, "
                "then ranked by interest fit, distance, price, rating, and novelty."
            ),
            trip_dna=build_trip_dna(context, intent),
            experience_bundle=build_experience_bundle(context, intent),
        )
