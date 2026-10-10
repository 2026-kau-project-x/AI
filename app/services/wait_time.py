"""대기시간 예측 모델.

Phase 3 에서 서울시설공단 장애인콜택시 공공데이터로 LightGBM 을 학습해 교체할 예정이다.
그 전까지는 규칙 기반 baseline 으로 "API 계약(입·출력 형태)"을 먼저 고정해 BE 연동을 진행한다.
모델 교체 시 WaitTimeModel 프로토콜만 지키면 엔드포인트 코드는 바뀌지 않는다.
"""

from datetime import datetime, timedelta, timezone
from typing import Protocol

from app.core.config import settings
from app.schemas.predict import PredictRequest, PredictResponse, Weather

# 한국은 서머타임이 없어서 고정 오프셋으로 충분하다 (Windows 에는 tz 데이터베이스가 없어 zoneinfo 회피)
KST = timezone(timedelta(hours=9))

# 아래 배율들은 모두 임시 가정치 — 학습 모델로 대체될 때까지 "방향성"만 표현한다
_WEATHER_FACTOR = {Weather.CLEAR: 1.0, Weather.RAIN: 1.2, Weather.SNOW: 1.5}
_RUSH_HOURS = {7, 8, 17, 18}  # 평일 출퇴근 시간대
_NIGHT_HOURS = {22, 23, 0, 1, 2, 3, 4, 5}  # 운행 차량이 적은 심야
_CI_RATIO = 0.3  # 신뢰구간 ±30%


class WaitTimeModel(Protocol):
    def predict(self, req: PredictRequest) -> PredictResponse: ...


def _to_kst(dt: datetime) -> datetime:
    return dt.replace(tzinfo=KST) if dt.tzinfo is None else dt.astimezone(KST)


class BaselineWaitTimeModel:
    """시간대·요일·날씨·수요 비율을 곱해서 대기시간을 추정하는 규칙 기반 모델."""

    name = "baseline-rules-v0"

    def predict(self, req: PredictRequest) -> PredictResponse:
        t = _to_kst(req.requested_at)
        weekend = t.weekday() >= 5

        factor = 1.0
        if not weekend and t.hour in _RUSH_HOURS:
            factor *= 1.3
        if t.hour in _NIGHT_HOURS:
            factor *= 1.2
        if weekend:
            factor *= 0.9
        factor *= _WEATHER_FACTOR[req.weather]

        # 수요/공급 비율: 요청이 차량보다 많을수록 대기가 길어진다. 극단값은 0.5~3배로 자른다
        if req.pending_requests is not None and req.available_vehicles is not None:
            ratio = req.pending_requests / max(req.available_vehicles, 1)
            factor *= min(max(ratio, 0.5), 3.0)

        wait = settings.base_wait_min * factor
        return PredictResponse(
            expected_wait_min=round(wait, 1),
            lower_min=round(wait * (1 - _CI_RATIO), 1),
            upper_min=round(wait * (1 + _CI_RATIO), 1),
            model=self.name,
        )


def get_wait_time_model() -> WaitTimeModel:
    """FastAPI Depends 로 주입. 학습 모델이 생기면 여기서 S3 아티팩트를 로드한 모델로 바꾼다."""
    return BaselineWaitTimeModel()
