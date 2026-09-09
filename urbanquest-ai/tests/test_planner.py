import asyncio
import unittest

from app.chat.service import ChatService
from app.maps.demo import DemoMapsProvider
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
        self.assertLessEqual(response.plan.estimated_cost, context.budget_destination)
        self.assertLessEqual(response.plan.duration_minutes, context.available_minutes)
        self.assertEqual(response.plan.currency, "INR")
        self.assertEqual(len(response.plan.days), 1)

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
        )

        response = asyncio.run(service.respond("Plan a 3 day historic trip", context))

        self.assertEqual(len(response.plan.days), 3)
        self.assertGreaterEqual(len(response.plan.days[0].activities), 2)


if __name__ == "__main__":
    unittest.main()
