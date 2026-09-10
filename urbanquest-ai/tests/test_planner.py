import asyncio
import unittest

from app.chat.service import ChatService
from app.maps.demo import DemoMapsProvider
from app.maps.google import GoogleMapsProvider
from app.planner.models import Location, TravelerContext
from app.planner.service import AdventurePlanner


class PlannerTests(unittest.TestCase):
    def test_chat_creates_budgeted_historical_plan(self) -> None:
        service = ChatService(AdventurePlanner(DemoMapsProvider()))
        context = TravelerContext(
            home=Location(country="USA", city="San Francisco"),
            destination=Location(country="India", city="Hyderabad"),
            home_currency="USD",
            destination_currency="INR",
            budget_home=40,
            budget_destination=3480,
            available_minutes=180,
        )

        response = asyncio.run(
            service.respond("Plan a cheap historical adventure for 3 hours", context)
        )

        self.assertTrue(response.plan.stops)
        self.assertTrue(response.plan.stops[0].place_query)
        self.assertIsNotNone(response.plan.stops[0].latitude)
        self.assertLessEqual(response.plan.estimated_cost, context.budget_destination)
        self.assertLessEqual(response.plan.duration_minutes, context.available_minutes)
        self.assertEqual(response.plan.currency, "INR")
        self.assertEqual(len(response.plan.days), 1)
        self.assertEqual(response.plan.days[0].date, None)
        self.assertEqual(response.plan.trip_dna.culture, 85)
        self.assertIn("Hyderabad", response.plan.experience_bundle.title)

    def test_demo_plan_uses_selected_destination(self) -> None:
        service = ChatService(AdventurePlanner(DemoMapsProvider()))
        context = TravelerContext(
            home=Location(country="Japan", city="Tokyo"),
            destination=Location(country="USA", city="San Francisco"),
            home_currency="JPY",
            destination_currency="USD",
            budget_home=10000,
            budget_destination=63,
            available_minutes=180,
        )

        response = asyncio.run(service.respond("Find something historic", context))

        self.assertIn("San Francisco", response.plan.stops[0].name)

    def test_multi_day_request_returns_day_by_day_itinerary(self) -> None:
        service = ChatService(AdventurePlanner(DemoMapsProvider()))
        context = TravelerContext(
            home=Location(country="USA", city="San Francisco"),
            destination=Location(country="India", city="Hyderabad"),
            home_currency="USD",
            destination_currency="INR",
            budget_home=400,
            budget_destination=34800,
            available_minutes=3 * 1440,
            departure_date="2026-10-20",
            return_date="2026-10-22",
        )

        response = asyncio.run(service.respond("Plan a 3 day historic trip", context))

        self.assertEqual(len(response.plan.days), 3)
        self.assertGreaterEqual(len(response.plan.days[0].activities), 2)
        self.assertEqual(
            [day.date for day in response.plan.days],
            ["2026-10-20", "2026-10-21", "2026-10-22"],
        )
        self.assertTrue(all(day.activities for day in response.plan.days))
        self.assertEqual(
            [experience.name for experience in response.plan.experience_bundle.experiences],
            [stop.name for stop in response.plan.stops],
        )

    def test_preferences_change_generated_plan(self) -> None:
        service = ChatService(AdventurePlanner(DemoMapsProvider()))
        context = TravelerContext(
            home=Location(country="USA", city="San Francisco"),
            destination=Location(country="India", city="Hyderabad"),
            home_currency="USD",
            destination_currency="INR",
            budget_home=100,
            budget_destination=8700,
            available_minutes=180,
        )

        history = asyncio.run(service.respond("Plan a historic trip", context)).plan
        food = asyncio.run(service.respond("Plan a food trip", context)).plan

        self.assertNotEqual(
            [stop.name for stop in history.stops],
            [stop.name for stop in food.stops],
        )
        self.assertEqual(food.trip_dna.food, 85)

    def test_demo_resolves_place_query_without_inventing_coordinates(self) -> None:
        place = asyncio.run(DemoMapsProvider().resolve_place("Charminar", "Hyderabad"))
        self.assertEqual(place.place_query, "Charminar, Hyderabad")
        self.assertEqual((place.latitude, place.longitude), (17.3616, 78.4747))

    def test_google_route_maps_response_to_route(self) -> None:
        provider = GoogleMapsProvider("test-key")

        async def fake_request(url, payload, headers):
            self.assertIn("computeRoutes", url)
            self.assertEqual(payload["travelMode"], "WALK")
            return {"routes": [{"distanceMeters": 1500, "duration": "180s"}]}

        provider._request = fake_request
        route = asyncio.run(provider.route((1, 2), (3, 4), "walking"))
        self.assertEqual(route.distance_km, 1.5)
        self.assertEqual(route.duration_minutes, 3)


if __name__ == "__main__":
    unittest.main()
