from typing import Optional

from pydantic import BaseModel, Field


class Place(BaseModel):
    place_query: str
    name: str
    description: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: str
    estimated_cost: float = Field(ge=0)
    duration_minutes: int = Field(gt=0)
    rating: float = Field(ge=0, le=5)
    novelty: float = Field(ge=0, le=1)
    distance_km: float = Field(ge=0)


class Route(BaseModel):
    distance_km: float = Field(ge=0)
    duration_minutes: int = Field(ge=0)
