import asyncio
import json
from urllib.request import Request, urlopen

from app.maps.models import Place, Route
from app.maps.provider import MapsProvider


class GoogleMapsProvider(MapsProvider):
    """Server-side Google Places (New) and Routes provider."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def resolve_place(self, place_query: str, city: str) -> Place:
        query = f"{place_query}, {city}"
        response = await self._request(
            "https://places.googleapis.com/v1/places:searchText",
            {"textQuery": query, "maxResultCount": 1},
            {"X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.rating,places.types"},
        )
        places = response.get("places", [])
        if not places:
            raise ValueError(f"Google Places returned no result for {query!r}")
        item = places[0]
        location = item.get("location", {})
        name = item.get("displayName", {}).get("text", place_query)
        return Place(
            place_query=query,
            name=name,
            description=item.get("formattedAddress", name),
            latitude=location["latitude"],
            longitude=location["longitude"],
            category=(item.get("types") or ["culture"])[0],
            estimated_cost=0,
            duration_minutes=45,
            rating=float(item.get("rating", 0)),
            novelty=0.5,
            distance_km=0,
        )

    async def nearby_places(
        self, latitude: float, longitude: float, radius: int, category: str, city: str
    ) -> list[Place]:
        del latitude, longitude, radius
        place = await self.resolve_place(f"{category} attractions", city)
        return [place]

    async def route(
        self, origin: tuple[float, float], destination: tuple[float, float], mode: str
    ) -> Route:
        travel_mode = {"walking": "WALK", "transit": "TRANSIT", "driving": "DRIVE"}.get(
            mode, "WALK"
        )
        response = await self._request(
            "https://routes.googleapis.com/directions/v2:computeRoutes",
            {
                "origin": {"location": {"latLng": {"latitude": origin[0], "longitude": origin[1]}}},
                "destination": {"location": {"latLng": {"latitude": destination[0], "longitude": destination[1]}}},
                "travelMode": travel_mode,
                "routingPreference": "TRAFFIC_AWARE" if travel_mode == "DRIVE" else "TRAFFIC_UNAWARE",
            },
            {"X-Goog-FieldMask": "routes.distanceMeters,routes.duration"},
        )
        routes = response.get("routes", [])
        if not routes:
            raise ValueError("Google Routes returned no route")
        route = routes[0]
        seconds = int(float(route.get("duration", "0s").rstrip("s")))
        return Route(
            distance_km=round(route.get("distanceMeters", 0) / 1000, 2),
            duration_minutes=max(1, round(seconds / 60)),
        )

    async def _request(self, url: str, payload: dict, extra_headers: dict) -> dict:
        def send() -> dict:
            request = Request(
                url,
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self.api_key,
                    **extra_headers,
                },
                method="POST",
            )
            with urlopen(request, timeout=15) as response:
                return json.loads(response.read())

        return await asyncio.to_thread(send)
