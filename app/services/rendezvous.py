"""랑데부(합류) 지점 최적화.

목표: 보행자와 이동지원차량이 "둘 다 도착하는 시각(max)"이 가장 빠른 지점을 고른다.
baseline 은 보행자→목적지 직선 위의 후보 11개(0%, 10%, … 100%)를 직선거리×우회계수로 평가한다.

Phase 3~4 개선 예정:
- 직선 대신 TMAP 보행 경로/차량 경로의 실제 거리·시간으로 평가
- 제약 조건: 차량 접근 가능한 도로, 보행자 횡단 최소화(안전)
"""

from typing import Protocol

from app.core.config import settings
from app.schemas.common import LatLng
from app.schemas.optimize import OptimizeRequest, OptimizeResponse
from app.services.geo import haversine_m, interpolate

_CANDIDATES = 10  # 구간 분할 수 → 후보는 0/10 ~ 10/10 의 11개


class RendezvousOptimizer(Protocol):
    def optimize(self, req: OptimizeRequest) -> OptimizeResponse: ...


class LineSearchOptimizer:
    name = "baseline-line-search-v0"

    def optimize(self, req: OptimizeRequest) -> OptimizeResponse:
        w, d, v = req.walker, req.destination, req.vehicle
        vehicle_mps = settings.vehicle_speed_kmh * 1000 / 3600

        best: tuple[float, float, float, float | None, float] | None = None
        for i in range(_CANDIDATES + 1):
            lat, lng = interpolate(w.lat, w.lng, d.lat, d.lng, i / _CANDIDATES)
            walk_m = haversine_m(w.lat, w.lng, lat, lng) * settings.walk_detour_factor
            walk_s = walk_m / settings.walk_speed_mps
            if v is None:
                # 차량 위치를 모르면 합류 시각을 비교할 수 없다 → 목적지(마지막 후보)까지 걷는다
                if i < _CANDIDATES:
                    continue
                veh_s = None
                meet_s = walk_s
            else:
                veh_s = haversine_m(v.lat, v.lng, lat, lng) * settings.vehicle_detour_factor / vehicle_mps
                meet_s = max(walk_s, veh_s)
            # 합류 시각이 같으면 먼저 평가된(= 덜 걷는) 후보를 유지 — 이동취약자의 보행 부담을 줄인다
            if best is None or meet_s < best[4]:
                best = (lat, lng, walk_m, veh_s, meet_s)

        assert best is not None
        lat, lng, walk_m, veh_s, meet_s = best
        return OptimizeResponse(
            rendezvous=LatLng(lat=lat, lng=lng),
            walk_distance_m=round(walk_m, 1),
            walk_eta_s=round(walk_m / settings.walk_speed_mps, 1),
            vehicle_eta_s=None if veh_s is None else round(veh_s, 1),
            meet_eta_s=round(meet_s, 1),
            strategy=self.name,
        )


def get_optimizer() -> RendezvousOptimizer:
    return LineSearchOptimizer()
