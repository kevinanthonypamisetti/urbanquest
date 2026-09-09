from app.maps.models import Place
from app.planner.models import TravelerContext, PlannerIntent


def score_place(
    place: Place, context: TravelerContext, intent: PlannerIntent
) -> float:
    preference = 1.0 if place.category == intent.category else 0.35
    distance = max(0.0, 1.0 - place.distance_km / 10)
    price = 1.0 if place.estimated_cost <= context.budget_destination else 0.0
    if intent.avoid_expensive:
        price = max(0.0, 1.0 - place.estimated_cost / max(context.budget_destination, 1))
    rating = place.rating / 5
    novelty = place.novelty if intent.adventurous else 1 - place.novelty / 2
    return (
        preference * 0.30
        + distance * 0.20
        + price * 0.20
        + rating * 0.15
        + novelty * 0.15
    )
