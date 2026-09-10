from typing import Optional

from pydantic import BaseModel, Field

from app.experience.models import ExperienceBundle, TripDNA


class Location(BaseModel):
    country: str
    state: Optional[str] = None
    city: str
    latitude: float = 0
    longitude: float = 0


class TravelerContext(BaseModel):
    home: Location
    destination: Location
    home_currency: str = Field(min_length=3, max_length=3)
    destination_currency: str = Field(min_length=3, max_length=3)
    budget_home: float = Field(ge=0)
    budget_destination: float = Field(ge=0)
    available_minutes: int = Field(gt=0)
    interests: list[str] = Field(default_factory=list)
    transport_mode: str = "walking"
    departure_date: Optional[str] = None
    return_date: Optional[str] = None
    travelers: int = Field(default=1, gt=0)


class PlannerIntent(BaseModel):
    category: str = "culture"
    duration_minutes: Optional[int] = Field(default=None, gt=0)
    avoid_expensive: bool = False
    adventurous: bool = False


class AdventureStop(BaseModel):
    place_query: str
    name: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    duration_minutes: int
    estimated_cost: float


class BudgetBreakdown(BaseModel):
    category: str
    amount: float = Field(ge=0)
    currency: str


class ItineraryDay(BaseModel):
    day: int
    date: Optional[str] = None
    title: str
    activities: list[AdventureStop]


class AdventurePlan(BaseModel):
    title: str
    description: str
    duration_minutes: int
    distance_km: float
    estimated_cost: float
    currency: str
    stops: list[AdventureStop]
    days: list[ItineraryDay]
    budget: list[BudgetBreakdown]
    reasoning: str
    trip_dna: TripDNA
    experience_bundle: ExperienceBundle
