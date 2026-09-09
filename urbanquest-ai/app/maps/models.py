from pydantic import BaseModel, Field


class Place(BaseModel):
    name: str
    description: str
    latitude: float
    longitude: float
    category: str
    estimated_cost: float = Field(ge=0)
    duration_minutes: int = Field(gt=0)
    rating: float = Field(ge=0, le=5)
    novelty: float = Field(ge=0, le=1)
    distance_km: float = Field(ge=0)


class Route(BaseModel):
    distance_km: float = Field(ge=0)
    duration_minutes: int = Field(ge=0)
