"""/optimize (랑데부 지점 최적화) 요청·응답 모델."""

from pydantic import BaseModel

from app.schemas.common import LatLng


class OptimizeRequest(BaseModel):
    walker: LatLng  # 보행자(사용자) 현재 위치
    destination: LatLng  # 사용자가 가려는 목적지
    # 이동지원차량 현재 위치. Dummy Vehicle API 연동 전에는 없을 수 있다
    vehicle: LatLng | None = None


class OptimizeResponse(BaseModel):
    rendezvous: LatLng
    walk_distance_m: float
    walk_eta_s: float
    vehicle_eta_s: float | None  # 차량 위치를 모르면 None
    meet_eta_s: float  # 둘 다 도착하는 시각 = max(보행, 차량)
    strategy: str
