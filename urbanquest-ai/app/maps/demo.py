from app.maps.models import Place, Route
from app.maps.provider import MapsProvider


DEMO_PLACES = [
    Place(
        name="Charminar",
        description="A landmark four-century-old monument at the heart of Hyderabad.",
        latitude=17.3616,
        longitude=78.4747,
        category="history",
        estimated_cost=80,
        duration_minutes=35,
        rating=4.7,
        novelty=0.65,
        distance_km=0.8,
    ),
    Place(
        name="Laad Bazaar",
        description="A lively lane of bangles, crafts, and local street life.",
        latitude=17.3612,
        longitude=78.4722,
        category="culture",
        estimated_cost=0,
        duration_minutes=30,
        rating=4.5,
        novelty=0.82,
        distance_km=1.0,
    ),
    Place(
        name="Nimrah Cafe",
        description="A relaxed local stop for Irani chai and fresh Osmania biscuits.",
        latitude=17.3605,
        longitude=78.4731,
        category="food",
        estimated_cost=120,
        duration_minutes=30,
        rating=4.4,
        novelty=0.7,
        distance_km=0.9,
    ),
    Place(
        name="Salar Jung Museum",
        description="A broad collection of art and historic objects beside the Musi River.",
        latitude=17.3714,
        longitude=78.4804,
        category="art",
        estimated_cost=200,
        duration_minutes=70,
        rating=4.6,
        novelty=0.55,
        distance_km=2.5,
    ),
]


class DemoMapsProvider(MapsProvider):
    async def nearby_places(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        category: str,
        city: str,
    ) -> list[Place]:
        del latitude, longitude, radius
        if city.lower() != "hyderabad":
            return [
                Place(
                    name=f"{city} {category.title()} Walk",
                    description=f"A locally minded {category} route through {city}.",
                    latitude=0,
                    longitude=0,
                    category=category,
                    estimated_cost=0,
                    duration_minutes=45,
                    rating=4.2,
                    novelty=0.7,
                    distance_km=1.2,
                )
            ]
        matches = [place for place in DEMO_PLACES if place.category == category]
        related = [place for place in DEMO_PLACES if place.category != category]
        return matches + related

    async def route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: str,
    ) -> Route:
        del origin, destination
        duration = 12 if mode == "walking" else 8
        return Route(distance_km=0.8, duration_minutes=duration)
