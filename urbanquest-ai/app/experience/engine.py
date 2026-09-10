from app.experience.models import ExperienceBundle, ExperienceNode, TripDNA
from app.planner.models import PlannerIntent, TravelerContext


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
    context: TravelerContext, intent: PlannerIntent
) -> ExperienceBundle:
    city = context.destination.city
    nodes = [
        ExperienceNode(
            name=f"Sunrise {city} walk",
            description="Start quietly, find a viewpoint, and let the city wake up.",
            tags=["adventure", "photography", "quiet"],
            duration_minutes=50,
            estimated_cost=0,
            distance_km=1.2,
        ),
        ExperienceNode(
            name=f"Local breakfast in {city}",
            description="A neighborhood breakfast chosen for local flavor rather than tourist traffic.",
            tags=["food", "local", "culture"],
            duration_minutes=45,
            estimated_cost=180,
            distance_km=0.8,
        ),
        ExperienceNode(
            name=f"Hidden {intent.category} trail",
            description="A flexible route connecting smaller places with time to linger.",
            tags=[intent.category, "local", "discovery"],
            duration_minutes=75,
            estimated_cost=250,
            distance_km=2.1,
        ),
        ExperienceNode(
            name=f"Golden-hour gathering in {city}",
            description="End the day with a view, a shared plate, and an unhurried route home.",
            tags=["food", "relaxation", "sunset"],
            duration_minutes=90,
            estimated_cost=450,
            distance_km=1.5,
        ),
    ]
    return ExperienceBundle(
        title=f"{city} through your Trip DNA",
        description="A connected sequence of moments, not a checklist of attractions.",
        experiences=nodes,
    )
