from pydantic import BaseModel, Field


class LatLng(BaseModel):
    """BE schemas/trip.py 의 LatLng 와 같은 형태 (BE ↔ AI 계약을 맞추기 위해)."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
