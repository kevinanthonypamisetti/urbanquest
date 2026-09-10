from pydantic import BaseModel, Field


class ExperienceNode(BaseModel):
    name: str
    description: str
    tags: list[str]
    duration_minutes: int = Field(gt=0)
    estimated_cost: float = Field(ge=0)
    distance_km: float = Field(ge=0)


class ExperienceBundle(BaseModel):
    title: str
    description: str
    experiences: list[ExperienceNode]


class TripDNA(BaseModel):
    adventure: int = Field(ge=0, le=100)
    food: int = Field(ge=0, le=100)
    nightlife: int = Field(ge=0, le=100)
    culture: int = Field(ge=0, le=100)
    relaxation: int = Field(ge=0, le=100)
    walking: str
    crowds: str
