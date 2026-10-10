"""좌표 계산 유틸 (FE route_models.dart 의 GeoPoint.distanceTo 와 같은 Haversine 공식)."""

import math

EARTH_RADIUS_M = 6_371_000.0


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 위경도 사이의 대원(최단) 거리(m)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def interpolate(lat1: float, lng1: float, lat2: float, lng2: float, t: float) -> tuple[float, float]:
    """두 점 사이를 t(0~1) 비율로 선형 보간. 수 km 이내 도심 거리에서는 오차가 무시할 수준이다."""
    return lat1 + (lat2 - lat1) * t, lng1 + (lng2 - lng1) * t
