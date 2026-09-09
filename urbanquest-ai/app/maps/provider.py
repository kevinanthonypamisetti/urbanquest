from abc import ABC, abstractmethod

from app.maps.models import Place, Route


class MapsProvider(ABC):
    @abstractmethod
    async def nearby_places(
        self,
        latitude: float,
        longitude: float,
        radius: int,
        category: str,
        city: str,
    ) -> list[Place]:
        raise NotImplementedError

    @abstractmethod
    async def route(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        mode: str,
    ) -> Route:
        raise NotImplementedError
