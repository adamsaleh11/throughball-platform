from pydantic import BaseModel

from app.models.health import ObservabilityMeta
from app.models.worldcup import City


class CityDetailResponse(BaseModel):
    city: City
    meta: ObservabilityMeta
