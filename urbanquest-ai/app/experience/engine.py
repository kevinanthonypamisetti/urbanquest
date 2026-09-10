from app.experience.models import ExperienceBundle, ExperienceNode, TripDNA
from app.planner.models import AdventureStop, PlannerIntent, TravelerContext


def build_trip_dna(context: TravelerContext, intent: PlannerIntent) -> TripDNA:
    preferences = " ".join(context.interests).lower()
    is_food = intent.category == "food" or "food" in preferences
    is_adventure = intent.adventurous or "adventure" in preferences
    is_culture = intent.category in {"history", "art", "culture"}
    return TripDNA(
        adventure=90 if is_adventure else 45,
        food=85 if is_food else 55,
        nightlife=70 if "night" in preferences else 30,
        culture=85 if is_culture else 50,
        relaxation=65 if "relax" in preferences else 25,
        walking="High" if context.transport_mode == "walking" else "Medium",
        crowds="Low" if intent.avoid_expensive else "Flexible",
    )


def build_experience_bundle(
    context: TravelerContext,
    intent: PlannerIntent,
    stops: list[AdventureStop],
) -> ExperienceBundle:
    city = context.destination.city
    nodes = [
        ExperienceNode(
            name=stop.name,
            description=stop.description,
            tags=[intent.category, "local", "discovery"],
            duration_minutes=stop.duration_minutes,
            estimated_cost=stop.estimated_cost,
            distance_km=0,
        )
        for stop in stops
    ]
    return ExperienceBundle(
        title=f"{city} through your Trip DNA",
        description=(
            f"{len(nodes)} real itinerary stops selected for your "
            f"{intent.category} preferences."
        ),
        experiences=nodes,
    )
