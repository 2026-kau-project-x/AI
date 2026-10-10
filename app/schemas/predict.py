"""/predict (대기시간 예측) 요청·응답 모델."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.common import LatLng


class Weather(str, Enum):
    CLEAR = "CLEAR"
    RAIN = "RAIN"
    SNOW = "SNOW"


class PredictRequest(BaseModel):
    # 타임존이 없으면 KST(한국 표준시)로 간주한다
    requested_at: datetime
    location: LatLng
    weather: Weather = Weather.CLEAR
    # 차량 수요 지표. 둘 다 있으면 "대기 중 요청 / 가용 차량" 비율을 반영한다
    pending_requests: int | None = Field(default=None, ge=0)
    available_vehicles: int | None = Field(default=None, ge=0)


class PredictResponse(BaseModel):
    expected_wait_min: float
    # 신뢰구간 (baseline 은 고정 비율 ±30%)
    lower_min: float
    upper_min: float
    model: str
