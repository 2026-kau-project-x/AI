# AI (FastAPI)

Project X AI 서비스. **대기시간 예측(/predict)** 과 **랑데부(합류) 지점 최적화(/optimize)** 를 담당한다.
BE 만 내부망으로 호출하는 Stateless 서비스이며(DB 없음) 외부에 공개하지 않는다. 포트 `8001`.

> 현재는 규칙 기반 **baseline** 이다. 목적은 "API 계약(입·출력 형태)"을 먼저 고정해 BE 연동을 진행하는 것.
> Phase 3 에서 학습 모델(LightGBM)·TMAP 실경로 질의로 교체해도 엔드포인트·계약은 그대로 둔다.

## 구조
```
app/
  main.py               앱 진입점
  core/config.py        환경설정 (속도·우회계수 등 baseline 가정치)
  api/v1/endpoints/     health, predict, optimize
  schemas/              요청·응답 모델 (pydantic, BE 와 같은 LatLng)
  services/
    wait_time.py        WaitTimeModel 프로토콜 + BaselineWaitTimeModel
    rendezvous.py       RendezvousOptimizer 프로토콜 + LineSearchOptimizer
    geo.py              Haversine 거리, 보간
tests/                  pytest
```

## 실행
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   /   macOS·Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env                       # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8001  # http://localhost:8001/docs
pytest
```

## API (v1)
| Method | Path | 설명 |
|---|---|---|
| GET | `/api/v1/health` | 헬스체크 (ECS) |
| POST | `/api/v1/predict` | 대기시간 예측 |
| POST | `/api/v1/optimize` | 랑데부 지점 최적화 (BE `HttpAiClient` 가 호출) |

### POST /api/v1/predict
```jsonc
// 요청 — requested_at 에 타임존이 없으면 KST 로 간주
{"requested_at": "2026-10-14T08:00:00+09:00", "location": {"lat": 37.56, "lng": 126.99},
 "weather": "CLEAR", "pending_requests": 12, "available_vehicles": 8}
// 응답
{"expected_wait_min": 58.5, "lower_min": 41.0, "upper_min": 76.1, "model": "baseline-rules-v0"}
```
baseline: `기준 30분 × 출퇴근(평일 7~8·17~18시) 1.3 × 심야(22~5시) 1.2 × 주말 0.9 × 날씨(비 1.2/눈 1.5) × 수요비율(0.5~3배)`.
**모든 배율은 임시 가정치**이며 서울시설공단 장애인콜택시 공공데이터 학습으로 대체한다.

### POST /api/v1/optimize
```jsonc
// 요청 — vehicle 은 Dummy Vehicle API 연동 전까지 생략 가능
{"walker": {"lat": 37.56, "lng": 126.99}, "destination": {"lat": 37.57, "lng": 126.99},
 "vehicle": {"lat": 37.58, "lng": 126.99}}
// 응답
{"rendezvous": {"lat": 37.562, "lng": 126.99}, "walk_distance_m": 266.9, "walk_eta_s": 296.5,
 "vehicle_eta_s": 403.5, "meet_eta_s": 403.5, "strategy": "baseline-line-search-v0"}
```
baseline: 보행자→목적지 직선 위 후보 11개(0%, 10%, … 100%) 중 `max(보행 ETA, 차량 ETA)` 가 최소인 지점. 동률이면 덜 걷는 쪽.
차량 위치가 없으면 목적지 자체를 반환한다. 보행 0.9 m/s(이동취약자 가정)·우회 1.2, 차량 25 km/h·우회 1.4.

## 다음 단계
- 공공데이터 수집(Airbyte → S3) → LightGBM 학습 → 모델 아티팩트를 S3 에서 로드 (`get_wait_time_model`)
- /optimize: 직선 대신 TMAP 보행·차량 경로 질의, 차량 접근 가능 도로·횡단 최소화 제약
- KPI(예측 MAE, 추론 지연)를 CloudWatch 메트릭으로 내보내기
